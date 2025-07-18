import { NextRequest, NextResponse } from 'next/server';
import { getDatabase } from '@/lib/mongodb';

export async function GET() {
  try {
    const db = await getDatabase();
    
    // Sample NFTs - in production, fetch from database
    const nfts = [
      {
        id: "meme_nft_1",
        name: "Crypto Meme #1",
        description: "Legendary Pepe Meme",
        price: 250,
        image_url: "https://via.placeholder.com/300x300/ff9ff3/ffffff?text=MEME+1",
        category: "meme",
        rarity: "legendary",
        is_listed: true,
        owner: null,
        created_at: new Date().toISOString()
      },
      {
        id: "meme_nft_2",
        name: "Crypto Meme #2",
        description: "Rare Doge Meme",
        price: 150,
        image_url: "https://via.placeholder.com/300x300/f1c40f/ffffff?text=MEME+2",
        category: "meme",
        rarity: "rare",
        is_listed: true,
        owner: null,
        created_at: new Date().toISOString()
      },
      {
        id: "meme_nft_3",
        name: "Bitcoin Jagd NFT",
        description: "Exklusive Bitcoin Jagd Sammelkarte",
        price: 500,
        image_url: "https://via.placeholder.com/300x300/3498db/ffffff?text=BITCOIN+JAGD",
        category: "game",
        rarity: "epic",
        is_listed: true,
        owner: null,
        created_at: new Date().toISOString()
      }
    ];

    return NextResponse.json(nfts);
  } catch (error) {
    console.error('Error loading NFTs:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}