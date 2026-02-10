-- 002: Add INSERT RLS policies for conversations and messages
-- The initial schema only had SELECT policies. Edge Functions use
-- the service-role key to bypass RLS for inserts, but these policies
-- are good practice for completeness and for any future client-side inserts.

CREATE POLICY "Users can insert own conversations"
    ON public.conversations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can insert own messages"
    ON public.messages FOR INSERT
    WITH CHECK (auth.uid() = user_id);
