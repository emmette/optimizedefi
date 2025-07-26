import { NextResponse } from 'next/server'
import { getNonce } from '@/lib/auth/session'

export async function GET() {
  try {
    const nonce = await getNonce()
    return NextResponse.json({ nonce })
  } catch (error) {
    console.error('Failed to generate nonce:', error)
    return NextResponse.json(
      { error: 'Failed to generate nonce' },
      { status: 500 }
    )
  }
}