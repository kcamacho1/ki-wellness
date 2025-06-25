import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabaseClient';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(req: Request) {
  const { user_id } = await req.json();

  const { data, error } = await supabase
    .from('food_journal')
    .select('*')
    .eq('user_id', user_id)
    .order('date', { ascending: false })
    .limit(50);

  if (error || !data) {
    return NextResponse.json({ error: 'Failed to load journal data' }, { status: 500 });
  }

  const prompt = `Here is a list of meals logged by a user. Identify any nutritional gaps (e.g. low protein, low fiber, etc.), and suggest 2 improvements:
  
${JSON.stringify(data, null, 2)}

Provide a friendly summary with nutrition tips.`;

  const completion = await openai.chat.completions.create({
    model: 'gpt-4',
    messages: [{ role: 'user', content: prompt }],
  });

  return NextResponse.json({ analysis: completion.choices[0].message.content });
}
