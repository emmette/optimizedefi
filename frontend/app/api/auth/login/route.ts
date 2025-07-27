import { NextRequest, NextResponse } from 'next/server'
import { verifySiweMessage, getSessionFromSiwe } from '@/lib/auth/siwe'
import { createUserSession, getSession } from '@/lib/auth/session'

export async function POST(request: NextRequest) {
  try {
    const { message, signature } = await request.json()

    if (!message || !signature) {
      return NextResponse.json(
        { error: 'Message and signature are required' },
        { status: 400 }
      )
    }

    // Verify the SIWE message
    const siweMessage = await verifySiweMessage(message, signature)
    
    if (!siweMessage) {
      return NextResponse.json(
        { error: 'Invalid signature' },
        { status: 401 }
      )
    }

    // Verify the nonce
    const session = await getSession()
    if (!session.nonce || siweMessage.nonce !== session.nonce) {
      return NextResponse.json(
        { error: 'Invalid nonce' },
        { status: 401 }
      )
    }

    // Verify domain
    const expectedDomain = new URL(request.url).hostname
    if (siweMessage.domain !== expectedDomain && siweMessage.domain !== 'localhost') {
      return NextResponse.json(
        { error: 'Invalid domain' },
        { status: 401 }
      )
    }

    // Create session
    const sessionData = getSessionFromSiwe(siweMessage)
    await createUserSession({ siwe: sessionData })

    // Clear the nonce after successful login
    session.nonce = undefined
    await session.save()

    // Call backend API to get JWT token
    let accessToken = null
    try {
      const backendResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          signature,
          address: siweMessage.address
        })
      })
      
      if (backendResponse.ok) {
        const backendData = await backendResponse.json()
        accessToken = backendData.access_token
      }
    } catch (error) {
      console.error('Failed to get backend JWT:', error)
    }

    return NextResponse.json({
      success: true,
      address: siweMessage.address,
      chainId: siweMessage.chainId,
      access_token: accessToken
    })
  } catch (error) {
    console.error('Login error:', error)
    return NextResponse.json(
      { error: 'Authentication failed' },
      { status: 500 }
    )
  }
}