import { NextRequest, NextResponse } from 'next/server';
import { getDatabase } from '@/lib/mongodb';

export async function POST(request: NextRequest) {
  try {
    const db = await getDatabase();
    const { wallet_address, airdrop_id } = await request.json();
    
    if (!wallet_address || !airdrop_id) {
      return NextResponse.json({ error: 'wallet_address and airdrop_id required' }, { status: 400 });
    }
    
    // Check if user already claimed (mock for demo)
    const existingClaim = await db.collection('airdrop_claims').findOne({
      wallet_address,
      airdrop_id
    });
    
    if (existingClaim) {
      return NextResponse.json({ error: 'Airdrop already claimed' }, { status: 400 });
    }
    
    // Create claim record
    const claimRecord = {
      id: crypto.randomUUID(),
      wallet_address,
      airdrop_id,
      amount: airdrop_id === 'welcome_bonus' ? 100 : airdrop_id === 'community_bonus' ? 75 : 50,
      claimed_at: new Date(),
      status: 'completed'
    };
    
    await db.collection('airdrop_claims').insertOne(claimRecord);
    
    return NextResponse.json({
      success: true,
      amount: claimRecord.amount,
      transaction_hash: `0x${crypto.randomUUID().replace(/-/g, '')}`,
      message: `Successfully claimed ${claimRecord.amount} MURAT tokens!`
    });
    
  } catch (error) {
    console.error('Error claiming airdrop:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}