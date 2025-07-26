import { NextResponse } from 'next/server'
import { getSession } from '@/lib/auth/session'

export async function GET() {
  try {
    const session = await getSession()
    
    if (!session.siwe) {
      return NextResponse.json(
        { authenticated: false },
        { status: 401 }
      )
    }

    // Check if session is expired
    if (session.siwe.expirationTime) {
      const expiration = new Date(session.siwe.expirationTime)
      if (expiration < new Date()) {
        await session.destroy()
        return NextResponse.json(
          { authenticated: false, error: 'Session expired' },
          { status: 401 }
        )
      }
    }

    return NextResponse.json({
      authenticated: true,
      address: session.siwe.address,
      chainId: session.siwe.chainId,
      issuedAt: session.siwe.issuedAt,
      expirationTime: session.siwe.expirationTime
    })
  } catch (error) {
    console.error('Session check error:', error)
    return NextResponse.json(
      { authenticated: false, error: 'Failed to check session' },
      { status: 500 }
    )
  }
}