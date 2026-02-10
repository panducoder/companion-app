import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { AccessToken } from "npm:livekit-server-sdk";

serve(async (req) => {
  // Verify auth
  const authHeader = req.headers.get("Authorization")!;
  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_ANON_KEY")!,
    { global: { headers: { Authorization: authHeader } } }
  );

  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();
  if (error || !user) {
    return new Response(JSON.stringify({ error: "Unauthorized" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  // Get user profile
  const { data: profile } = await supabase
    .from("profiles")
    .select("name, companion_name")
    .eq("id", user.id)
    .single();

  // Create LiveKit room token
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

  // Create conversation record
  const { data: conversation } = await supabase
    .from("conversations")
    .insert({ user_id: user.id })
    .select()
    .single();

  return new Response(
    JSON.stringify({
      token: await token.toJwt(),
      url: Deno.env.get("LIVEKIT_URL"),
      roomName,
      conversationId: conversation?.id,
    }),
    { headers: { "Content-Type": "application/json" } }
  );
});
