import { NextResponse } from 'next/server';
import { supabase } from '@/lib/supabaseClient';

const lookupLog = new Map<string, number>();
const RATE_LIMIT_MS = 10_000; // 10 seconds per IP
const OPENFOODFACTS_API = 'https://world.openfoodfacts.org/cgi/search.pl';
const NUTRITIONIX_API = 'https://trackapi.nutritionix.com/v2/natural/nutrients';

export async function POST(req: Request) {
  const ip = req.headers.get('x-forwarded-for') || 'anon';
  const lastLookup = lookupLog.get(ip);
  const now = Date.now();

  if (lastLookup && now - lastLookup < RATE_LIMIT_MS) {
    return NextResponse.json({ error: 'Too many requests. Please wait a moment.' }, { status: 429 });
  }

  lookupLog.set(ip, now);

  const { food } = await req.json();

  if (!food || food.length < 2) {
    return NextResponse.json({ error: 'Invalid input' }, { status: 400 });
  }

  const lowerName = food.toLowerCase();

  // STEP 1: Check Supabase Cache
  const { data: cached } = await supabase
    .from('food_cache')
    .select('*')
    .ilike('name', lowerName)
    .limit(1)
    .single();

  if (cached) {
    return NextResponse.json({ ...cached, source: 'cache' });
  }

  // STEP 2: Try OpenFoodFacts
  const url = `${OPENFOODFACTS_API}?search_terms=${encodeURIComponent(food)}&search_simple=1&json=1`;
  const openRes = await fetch(url);

  if (
    openRes.ok &&
    openRes.headers.get('content-type')?.includes('application/json')
  ) {
    try {
      const openData = await openRes.json();
      const firstProduct = openData?.products?.[0];

      if (firstProduct?.nutriments) {
        const result = {
          name: food,
          protein_g: firstProduct.nutriments.proteins_100g || 0,
          carbs_g: firstProduct.nutriments.carbohydrates_100g || 0,
          fat_g: firstProduct.nutriments.fat_100g || 0,
          calories:
            firstProduct.nutriments.energy_kcal_100g ??
            firstProduct.nutriments['energy-kcal_100g'] ??
            (firstProduct.nutriments.energy_100g
                ? Math.round(firstProduct.nutriments.energy_100g / 4.184) // kJ → kcal
                : 0),
          api_source: 'openfoodfacts'
        };

        await supabase.from('food_cache').insert(result);
        return NextResponse.json({ ...result, source: 'openfoodfacts' });
      }
    } catch (err) {
      console.warn('⚠️ Failed to parse OpenFoodFacts JSON:', err);
    }
  } else {
    console.warn('⚠️ OpenFoodFacts returned non-JSON or failed for:', food);
  }

  // STEP 3: Fallback to Nutritionix
  const nutriRes = await fetch(NUTRITIONIX_API, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-app-id': process.env.NEXT_PUBLIC_NUTRITIONIX_APP_ID!,
      'x-app-key': process.env.NEXT_PUBLIC_NUTRITIONIX_APP_KEY!
    },
    body: JSON.stringify({ query: food })
  });

  const nutriData = await nutriRes.json();
  const item = nutriData?.foods?.[0];

  if (item) {
    const result = {
      name: item.food_name,
      protein_g: item.protein || 0,
      carbs_g: item.total_carbohydrate || 0,
      fat_g: item.total_fat || 0,
      calories: item.nf_calories || 0,
      api_source: 'nutritionix'
    };

    await supabase.from('food_cache').insert(result);
    return NextResponse.json({ ...result, source: 'nutritionix' });
  }

  return NextResponse.json({ error: 'No nutrition data found' }, { status: 404 });
}
