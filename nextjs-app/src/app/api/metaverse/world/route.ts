import { NextRequest, NextResponse } from 'next/server';
import { getDatabase } from '@/lib/mongodb';

export async function GET() {
  try {
    const db = await getDatabase();
    
    const worldData = {
      world_name: "KryptoMurat Metaverse",
      areas: [
        {
          id: "live_stream",
          name: "Live Stream Arena",
          description: "Zentrale Streaming-Bühne",
          position: { x: 0, y: 0 },
          access_level: "public"
        },
        {
          id: "nft_gallery",
          name: "NFT Gallery",
          description: "Exklusive NFT-Sammlung",
          position: { x: -200, y: 0 },
          access_level: "nft_required"
        },
        {
          id: "voting_chamber",
          name: "Voting Chamber",
          description: "Community-Governance",
          position: { x: -200, y: -100 },
          access_level: "public"
        },
        {
          id: "airdrop_zone",
          name: "Airdrop Zone",
          description: "MURAT Token Belohnungen",
          position: { x: 200, y: 0 },
          access_level: "public"
        },
        {
          id: "vip_lounge",
          name: "VIP Lounge",
          description: "Exklusiver VIP-Bereich",
          position: { x: 200, y: -100 },
          access_level: "premium"
        }
      ]
    };

    return NextResponse.json(worldData);
  } catch (error) {
    console.error('Error loading world data:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}