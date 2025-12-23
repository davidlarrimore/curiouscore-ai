import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

interface RequestBody {
  messages: Message[];
  systemPrompt: string;
  challengeTitle: string;
  currentPhase: number;
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { messages, systemPrompt, challengeTitle, currentPhase }: RequestBody = await req.json();
    const LOVABLE_API_KEY = Deno.env.get("LOVABLE_API_KEY");
    
    if (!LOVABLE_API_KEY) {
      throw new Error("LOVABLE_API_KEY is not configured");
    }

    console.log(`[chat-instructor] Processing chat for challenge: ${challengeTitle}, phase: ${currentPhase}`);
    console.log(`[chat-instructor] Message count: ${messages.length}`);

    // Build the enhanced system prompt with phase tracking and response format instructions
    const enhancedSystemPrompt = `${systemPrompt}

IMPORTANT RESPONSE FORMAT INSTRUCTIONS:
You are an interactive AI instructor. Your responses should include structured metadata for the learning platform.

At the END of each response, you MUST include a JSON block wrapped in <metadata> tags with the following format:
<metadata>
{
  "questionType": "text" | "mcq",
  "options": ["Option A", "Option B", "Option C", "Option D"] | null,
  "correctAnswer": 0 | 1 | 2 | 3 | null,
  "phase": ${currentPhase},
  "progressIncrement": 0-20,
  "scoreChange": -10 to 20,
  "hint": "A helpful hint if the student seems stuck" | null,
  "isComplete": boolean
}
</metadata>

- questionType: Use "mcq" when asking a multiple choice question, "text" for open-ended
- options: Provide exactly 4 options for MCQ, null for text questions
- correctAnswer: Index (0-3) of correct option for MCQ, null for text
- phase: Current learning phase (1-5 typically)
- progressIncrement: How much progress to add (0-20 based on response quality)
- scoreChange: Points to add/subtract based on answer correctness
- hint: Provide if the student made mistakes or seems confused
- isComplete: true only when the entire challenge is completed successfully

Current phase: ${currentPhase}
Challenge: ${challengeTitle}

Begin by greeting the student and introducing the first topic if this is the start, or continue from where they left off.`;

    const response = await fetch("https://ai.gateway.lovable.dev/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${LOVABLE_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "google/gemini-2.5-flash",
        messages: [
          { role: "system", content: enhancedSystemPrompt },
          ...messages,
        ],
        stream: true,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[chat-instructor] AI gateway error: ${response.status}`, errorText);
      
      if (response.status === 429) {
        return new Response(JSON.stringify({ error: "Rate limit exceeded. Please try again in a moment." }), {
          status: 429,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }
      if (response.status === 402) {
        return new Response(JSON.stringify({ error: "Usage limit reached. Please add credits to continue." }), {
          status: 402,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }
      
      return new Response(JSON.stringify({ error: "AI service temporarily unavailable" }), {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    console.log(`[chat-instructor] Streaming response started`);

    return new Response(response.body, {
      headers: { ...corsHeaders, "Content-Type": "text/event-stream" },
    });
  } catch (error) {
    console.error("[chat-instructor] Error:", error);
    return new Response(JSON.stringify({ error: error instanceof Error ? error.message : "Unknown error" }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
