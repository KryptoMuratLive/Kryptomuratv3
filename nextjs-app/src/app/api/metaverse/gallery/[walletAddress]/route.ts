import { NextRequest, NextResponse } from 'next/server';
import { getDatabase } from '@/lib/mongodb';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ walletAddress: string }> }
) {
  try {
    const { walletAddress } = await params;
    const db = await getDatabase();
    
    // Get NFTs owned by user
    const ownedNfts = await db.collection('metaverse_nfts').find({ owner: walletAddress }).toArray();
    
    // Get NFTs from purchases
    const purchases = await db.collection('nft_purchases').find({ wallet_address: walletAddress }).toArray();
    
    // Calculate total spent
    const totalSpent = purchases.reduce((sum, purchase) => sum + (purchase.price || 0), 0);
    
    return NextResponse.json({
      owned_nfts: ownedNfts,
      total_owned: ownedNfts.length,
      total_spent: totalSpent
    });
    
  } catch (error) {
    console.error('Error loading user gallery:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}