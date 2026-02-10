// generate-room-token/index.ts
// Creates a LiveKit room token for authenticated users and records the conversation.
//
// Required env vars (set via Supabase Dashboard > Edge Functions > Secrets):
//   SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY
//   LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL
//
// Deployment:
//   1. Install Supabase CLI: brew install supabase/tap/supabase
//   2. Link project:  supabase link --project-ref vkybqfcadvgiuhrkugrb
//   3. Set secrets:   supabase secrets set LIVEKIT_API_KEY=APIG6dqdGN9mUaA \
//                       LIVEKIT_API_SECRET=<secret> LIVEKIT_URL=wss://koi-ve3if36d.livekit.cloud
//   4. Deploy:        supabase functions deploy generate-room-token --no-verify-jwt
//      (JWT is verified in-code; set --no-verify-jwt so we can return proper JSON 401s
//       instead of Supabase's generic HTML 401 page)
//   5. Or keep verify_jwt=true in config.toml and deploy without --no-verify-jwt.

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { AccessToken } from "npm:livekit-server-sdk";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    // 1. Verify auth -------------------------------------------------------
    const authHeader = req.headers.get("Authorization");
    if (!authHeader) {
      return new Response(
        JSON.stringify({ error: "Missing authorization header" }),
        {
          status: 401,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_ANON_KEY")!,
      { global: { headers: { Authorization: authHeader } } }
    );

    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return new Response(JSON.stringify({ error: "Unauthorized" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // 2. Get user profile ---------------------------------------------------
    const { data: profile } = await supabase
      .from("profiles")
      .select("name, companion_name")
      .eq("id", user.id)
      .single();

    // 3. Create LiveKit room token ------------------------------------------
    const roomName = `koi-${user.id}-${Date.now()}`;
    const token = new AccessToken(
      Deno.env.get("LIVEKIT_API_KEY")!,
      Deno.env.get("LIVEKIT_API_SECRET")!,
      {
        identity: user.id,
        name: profile?.name || "User",
        metadata: JSON.stringify({
          user_id: user.id,
          user_name: profile?.name,
          companion_name: profile?.companion_name,
        }),
      }
    );

    token.addGrant({
      room: roomName,
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
    });

    // 4. Create conversation record -----------------------------------------
    // Use service-role client so the INSERT bypasses RLS
    // (the RLS policies only allow SELECT for conversations)
    const adminClient = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    );

    const { data: conversation, error: convError } = await adminClient
      .from("conversations")
      .insert({ user_id: user.id })
      .select()
      .single();

    if (convError) {
      console.error("Failed to create conversation:", convError);
      // Non-fatal: still return the token so the user can connect
    }

    // 5. Return token -------------------------------------------------------
    const jwt = await token.toJwt();

    return new Response(
      JSON.stringify({
        token: jwt,
        url: Deno.env.get("LIVEKIT_URL"),
        roomName,
        conversationId: conversation?.id ?? null,
      }),
      {
        status: 200,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  } catch (err) {
    console.error("Unexpected error in generate-room-token:", err);
    return new Response(
      JSON.stringify({ error: "Internal server error" }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});
