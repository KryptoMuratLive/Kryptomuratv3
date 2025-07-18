import { NextRequest, NextResponse } from 'next/server';
import { getDatabase } from '@/lib/mongodb';

export async function POST(request: NextRequest) {
  try {
    const db = await getDatabase();
    const { wallet_address, proposal_id, vote_option } = await request.json();
    
    if (!wallet_address || !proposal_id || !vote_option) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
    }
    
    // Check if user already voted
    const existingVote = await db.collection('metaverse_votes').findOne({
      wallet_address,
      proposal_id
    });
    
    if (existingVote) {
      // Update existing vote
      await db.collection('metaverse_votes').updateOne(
        { _id: existingVote._id },
        { 
          $set: {
            vote_option,
            updated_at: new Date()
          }
        }
      );
    } else {
      // Create new vote
      const voteRecord = {
        id: crypto.randomUUID(),
        wallet_address,
        proposal_id,
        vote_option,
        vote_weight: 1, // Can be enhanced with token-based voting power
        created_at: new Date()
      };
      
      await db.collection('metaverse_votes').insertOne(voteRecord);
    }
    
    return NextResponse.json({ success: true, message: 'Vote cast successfully' });
    
  } catch (error) {
    console.error('Error casting vote:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}