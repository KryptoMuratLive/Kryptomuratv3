import { NextRequest, NextResponse } from 'next/server';
import { getDatabase } from '@/lib/mongodb';

export async function POST(request: NextRequest) {
  try {
    const db = await getDatabase();
    const { wallet_address, nft_id } = await request.json();
    
    if (!wallet_address || !nft_id) {
      return NextResponse.json({ error: 'wallet_address and nft_id required' }, { status: 400 });
    }
    
    // Mock NFT data
    const nftPrices: { [key: string]: number } = {
      'meme_nft_1': 250,
      'meme_nft_2': 150,
      'meme_nft_3': 500
    };
    
    const nftNames: { [key: string]: string } = {
      'meme_nft_1': 'Crypto Meme #1',
      'meme_nft_2': 'Crypto Meme #2',
      'meme_nft_3': 'Bitcoin Jagd NFT'
    };
    
    const price = nftPrices[nft_id] || 100;
    const name = nftNames[nft_id] || 'Unknown NFT';
    
    // Create purchase record
    const purchaseRecord = {
      id: crypto.randomUUID(),
      wallet_address,
      nft_id,
      price,
      purchased_at: new Date(),
      transaction_hash: `0x${crypto.randomUUID().replace(/-/g, '')}`,
      status: 'completed'
    };
    
    await db.collection('nft_purchases').insertOne(purchaseRecord);
    
    // Update NFT ownership in database
    await db.collection('metaverse_nfts').updateOne(
      { id: nft_id },
      { 
        $set: {
          owner: wallet_address,
          is_listed: false,
          sold_at: new Date()
        }
      },
      { upsert: true }
    );
    
    return NextResponse.json({
      success: true,
      nft: { id: nft_id, name, price },
      transaction_hash: purchaseRecord.transaction_hash,
      message: `Successfully purchased ${name} for ${price} MURAT!`
    });
    
  } catch (error) {
    console.error('Error purchasing NFT:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}