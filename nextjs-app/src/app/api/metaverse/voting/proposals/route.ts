import { NextRequest, NextResponse } from 'next/server';
import { getDatabase } from '@/lib/mongodb';

export async function GET() {
  try {
    const db = await getDatabase();
    
    // Sample proposals - in production, fetch from database
    const proposals = [
      {
        id: "proposal_1",
        title: "Neue NFT-Kollektion",
        description: "Sollen wir eine neue Meme-NFT-Kollektion erstellen?",
        options: ["Ja", "Nein", "Später"],
        is_active: true,
        created_at: new Date().toISOString(),
        ends_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString() // 7 days from now
      },
      {
        id: "proposal_2",
        title: "Stream-Thema",
        description: "Welches Thema soll der nächste Stream haben?",
        options: ["Crypto News", "Gaming", "NFT Reviews"],
        is_active: true,
        created_at: new Date().toISOString(),
        ends_at: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString() // 3 days from now
      },
      {
        id: "proposal_3",
        title: "Metaverse Erweiterung",
        description: "Welche neue Bereiche sollen im Metaverse hinzugefügt werden?",
        options: ["Gaming Zone", "Trading Floor", "Social Hub"],
        is_active: true,
        created_at: new Date().toISOString(),
        ends_at: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString() // 5 days from now
      }
    ];

    return NextResponse.json(proposals);
  } catch (error) {
    console.error('Error loading proposals:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}