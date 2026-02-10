// delete-user-data/index.ts
// Cascading deletion of all user data: messages -> conversations -> pinecone -> profile -> auth user.
//
// Required env vars (set via Supabase Dashboard > Edge Functions > Secrets):
//   SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY
//   PINECONE_API_KEY, PINECONE_HOST (optional -- skipped if not set)
//
// IMPORTANT: The secret must be named SUPABASE_SERVICE_ROLE_KEY (not SUPABASE_SERVICE_KEY).
//   supabase secrets set SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
//
// Deployment:
//   1. Install Supabase CLI: brew install supabase/tap/supabase
//   2. Link project:  supabase link --project-ref vkybqfcadvgiuhrkugrb
//   3. Set secrets:   supabase secrets set SUPABASE_SERVICE_ROLE_KEY=<key> \
//                       PINECONE_API_KEY=<key> PINECONE_HOST=<host>
//   4. Deploy:        supabase functions deploy delete-user-data

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    // Verify auth using the user's JWT
    const authHeader = req.headers.get("Authorization");
    if (!authHeader) {
      return new Response(
        JSON.stringify({ error: "Missing authorization header" }),
        { status: 401, headers: { ...corsHeaders, "Content-Type": "application/json" } }
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
      return new Response(
        JSON.stringify({ error: "Unauthorized" }),
        { status: 401, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const userId = user.id;

    // Use service role client for admin operations (cascade deletion)
    const adminClient = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    );

    // Step 1: Delete messages belonging to this user
    const { error: messagesError } = await adminClient
      .from("messages")
      .delete()
      .eq("user_id", userId);

    if (messagesError) {
      console.error("Failed to delete messages:", messagesError);
      return new Response(
        JSON.stringify({ error: "Failed to delete messages" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Step 2: Delete conversations belonging to this user
    const { error: conversationsError } = await adminClient
      .from("conversations")
      .delete()
      .eq("user_id", userId);

    if (conversationsError) {
      console.error("Failed to delete conversations:", conversationsError);
      return new Response(
        JSON.stringify({ error: "Failed to delete conversations" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Step 3: Delete Pinecone vectors for this user
    const pineconeApiKey = Deno.env.get("PINECONE_API_KEY");
    const pineconeIndex = Deno.env.get("PINECONE_INDEX") || "koi-memories";
    const pineconeHost = Deno.env.get("PINECONE_HOST");

    if (pineconeApiKey && pineconeHost) {
      try {
        const pineconeResponse = await fetch(
          `https://${pineconeHost}/vectors/delete`,
          {
            method: "POST",
            headers: {
              "Api-Key": pineconeApiKey,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              filter: { user_id: { "$eq": userId } },
            }),
          }
        );

        if (!pineconeResponse.ok) {
          console.error(
            "Pinecone deletion failed:",
            pineconeResponse.status,
            await pineconeResponse.text()
          );
          // Continue with remaining deletions even if Pinecone fails
        }
      } catch (pineconeError) {
        console.error("Pinecone request failed:", pineconeError);
        // Continue — Pinecone cleanup can be retried later
      }
    }

    // Step 4: Delete profile
    const { error: profileError } = await adminClient
      .from("profiles")
      .delete()
      .eq("id", userId);

    if (profileError) {
      console.error("Failed to delete profile:", profileError);
      return new Response(
        JSON.stringify({ error: "Failed to delete profile" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Step 5: Delete auth user via admin API
    const { error: authDeleteError } = await adminClient.auth.admin.deleteUser(userId);

    if (authDeleteError) {
      console.error("Failed to delete auth user:", authDeleteError);
      return new Response(
        JSON.stringify({ error: "Failed to delete auth user" }),
        { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    return new Response(
      JSON.stringify({ success: true, message: "All user data deleted" }),
      { status: 200, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (err) {
    console.error("Unexpected error in delete-user-data:", err);
    return new Response(
      JSON.stringify({ error: "Internal server error" }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
