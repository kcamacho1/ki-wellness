// app/api/ai-nutrition-analysis/route.ts

import { NextResponse } from 'next/server';
import { OpenAI } from 'openai'; // or use openrouter or other platform

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export async function POST(req: Request) {
  const { entries } = await req.json();

  const formatted = entries.map(e => 
    `Date: ${e.date}, Food: ${e.food_name}, Protein: ${e.protein_g}g, Carbs: ${e.carbs_g}g, Fat: ${e.fat_g}g, Calories: ${e.calories}`
  ).join('\n');

  const prompt = `
You are a certified nutritionist. Analyze this food journal for patterns, achievements, possible nutrient gaps, and personalized suggestions.
Keep the summary concise and user-friendly.

Food Journal:
${formatted}

Return a short summary with:
- Achievements ✅
- Gaps ⚠️
- Recommendations 💡
`;

  const completion = await openai.chat.completions.create({
    model: 'gpt-3.5-turbo', // or any model from your provider
    messages: [{ role: 'user', content: prompt }],
    temperature: 0.7
  });

  const message = completion.choices[0]?.message?.content;

  return NextResponse.json({ message });
}
