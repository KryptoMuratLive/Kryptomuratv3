import { NextRequest, NextResponse } from 'next/server';
import { getDatabase } from '@/lib/mongodb';

export async function GET() {
  try {
    const db = await getDatabase();
    
    // Sample airdrops - in production, fetch from database
    const airdrops = [
      {
        id: "daily_bonus",
        name: "Daily Bonus",
        description: "Täglicher MURAT Bonus",
        amount: 50,
        image_url: "https://via.placeholder.com/150x150/ff6b6b/ffffff?text=DAILY",
        is_active: true,
        created_at: new Date().toISOString()
      },
      {
        id: "welcome_bonus",
        name: "Welcome Bonus",
        description: "Willkommensbonus für neue User",
        amount: 100,
        image_url: "https://via.placeholder.com/150x150/4ecdc4/ffffff?text=WELCOME",
        is_active: true,
        created_at: new Date().toISOString()
      },
      {
        id: "community_bonus",
        name: "Community Bonus",
        description: "Bonus für aktive Community-Mitglieder",
        amount: 75,
        image_url: "https://via.placeholder.com/150x150/45b7d1/ffffff?text=COMMUNITY",
        is_active: true,
        created_at: new Date().toISOString()
      }
    ];

    return NextResponse.json(airdrops);
  } catch (error) {
    console.error('Error loading airdrops:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}