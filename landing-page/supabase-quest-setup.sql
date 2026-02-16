-- ============================================================
-- AgentWallet Quest Campaign — Supabase SQL Setup
-- Run this entire file in the Supabase SQL Editor (Dashboard)
-- ============================================================

-- ======================== TABLES ========================

-- Quest users (profile for each authenticated user)
CREATE TABLE IF NOT EXISTS quest_users (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email text,
  display_name text,
  total_points integer DEFAULT 0,
  current_streak integer DEFAULT 0,
  longest_streak integer DEFAULT 0,
  last_checkin_date date,
  referral_code text UNIQUE,
  referred_by text,
  device_fingerprint text,
  created_at timestamptz DEFAULT now()
);

-- Quest definitions
CREATE TABLE IF NOT EXISTS quest_definitions (
  id text PRIMARY KEY,
  name text NOT NULL,
  description text,
  category text NOT NULL,
  points integer NOT NULL DEFAULT 0,
  quest_type text NOT NULL DEFAULT 'one_time' CHECK (quest_type IN ('one_time','daily')),
  prerequisites text[] DEFAULT '{}',
  cooldown_seconds integer DEFAULT 0,
  requires_proof boolean DEFAULT false,
  requires_review boolean DEFAULT false,
  enabled boolean DEFAULT true
);

-- Quest completions
CREATE TABLE IF NOT EXISTS quest_completions (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES quest_users(id) ON DELETE CASCADE,
  quest_id text NOT NULL REFERENCES quest_definitions(id),
  points_awarded integer NOT NULL DEFAULT 0,
  proof_url text,
  proof_data jsonb,
  status text NOT NULL DEFAULT 'completed' CHECK (status IN ('completed','pending_review','approved','rejected')),
  created_at timestamptz DEFAULT now(),
  UNIQUE(user_id, quest_id)
);

-- Quest attempts (for cooldown enforcement)
CREATE TABLE IF NOT EXISTS quest_attempts (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES quest_users(id) ON DELETE CASCADE,
  quest_id text NOT NULL REFERENCES quest_definitions(id),
  started_at timestamptz DEFAULT now()
);

-- Daily check-ins
CREATE TABLE IF NOT EXISTS daily_checkins (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES quest_users(id) ON DELETE CASCADE,
  checkin_date date NOT NULL DEFAULT CURRENT_DATE,
  points_awarded integer NOT NULL DEFAULT 50,
  streak_count integer NOT NULL DEFAULT 1,
  created_at timestamptz DEFAULT now(),
  UNIQUE(user_id, checkin_date)
);

-- Quiz questions pool
CREATE TABLE IF NOT EXISTS quiz_questions (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  question text NOT NULL,
  options jsonb NOT NULL,
  correct_index integer NOT NULL,
  enabled boolean DEFAULT true
);

-- Quiz attempts
CREATE TABLE IF NOT EXISTS quiz_attempts (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES quest_users(id) ON DELETE CASCADE,
  answers jsonb NOT NULL,
  score integer NOT NULL,
  total integer NOT NULL,
  passed boolean NOT NULL DEFAULT false,
  created_at timestamptz DEFAULT now()
);

-- Referrals
CREATE TABLE IF NOT EXISTS referrals (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  referrer_id uuid NOT NULL REFERENCES quest_users(id) ON DELETE CASCADE,
  referred_id uuid NOT NULL REFERENCES quest_users(id) ON DELETE CASCADE,
  points_awarded integer NOT NULL DEFAULT 200,
  created_at timestamptz DEFAULT now(),
  UNIQUE(referred_id)
);

-- User achievements
CREATE TABLE IF NOT EXISTS user_achievements (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES quest_users(id) ON DELETE CASCADE,
  achievement_id text NOT NULL,
  unlocked_at timestamptz DEFAULT now(),
  UNIQUE(user_id, achievement_id)
);

-- Activity feed
CREATE TABLE IF NOT EXISTS activity_feed (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_display text NOT NULL,
  action_text text NOT NULL,
  points integer DEFAULT 0,
  created_at timestamptz DEFAULT now()
);

-- Quest verifications (cross-page: docs scroll, dashboard login)
CREATE TABLE IF NOT EXISTS quest_verifications (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES quest_users(id) ON DELETE CASCADE,
  quest_id text NOT NULL,
  verification_data jsonb,
  created_at timestamptz DEFAULT now(),
  UNIQUE(user_id, quest_id)
);

-- ======================== INDEXES ========================

CREATE INDEX IF NOT EXISTS idx_quest_completions_user ON quest_completions(user_id);
CREATE INDEX IF NOT EXISTS idx_quest_completions_quest ON quest_completions(quest_id);
CREATE INDEX IF NOT EXISTS idx_quest_attempts_user_quest ON quest_attempts(user_id, quest_id);
CREATE INDEX IF NOT EXISTS idx_daily_checkins_user ON daily_checkins(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_feed_created ON activity_feed(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_quest_verifications_user ON quest_verifications(user_id);

-- ======================== RLS POLICIES ========================

ALTER TABLE quest_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE quest_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE quest_completions ENABLE ROW LEVEL SECURITY;
ALTER TABLE quest_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_checkins ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE referrals ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_feed ENABLE ROW LEVEL SECURITY;
ALTER TABLE quest_verifications ENABLE ROW LEVEL SECURITY;

-- quest_users
CREATE POLICY "quest_users_select" ON quest_users FOR SELECT TO authenticated USING (true);
CREATE POLICY "quest_users_insert" ON quest_users FOR INSERT TO authenticated WITH CHECK (auth.uid() = id);
CREATE POLICY "quest_users_update" ON quest_users FOR UPDATE TO authenticated USING (auth.uid() = id);

-- quest_definitions (read-only for all)
CREATE POLICY "quest_definitions_select" ON quest_definitions FOR SELECT TO authenticated USING (true);

-- quest_completions
CREATE POLICY "quest_completions_select" ON quest_completions FOR SELECT TO authenticated USING (true);
CREATE POLICY "quest_completions_insert" ON quest_completions FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);

-- quest_attempts
CREATE POLICY "quest_attempts_select" ON quest_attempts FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY "quest_attempts_insert" ON quest_attempts FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);

-- daily_checkins
CREATE POLICY "daily_checkins_select" ON daily_checkins FOR SELECT TO authenticated USING (true);
CREATE POLICY "daily_checkins_insert" ON daily_checkins FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);

-- quiz_questions (read-only)
CREATE POLICY "quiz_questions_select" ON quiz_questions FOR SELECT TO authenticated USING (true);

-- quiz_attempts
CREATE POLICY "quiz_attempts_select" ON quiz_attempts FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY "quiz_attempts_insert" ON quiz_attempts FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);

-- referrals
CREATE POLICY "referrals_select" ON referrals FOR SELECT TO authenticated USING (true);

-- user_achievements
CREATE POLICY "user_achievements_select" ON user_achievements FOR SELECT TO authenticated USING (true);

-- activity_feed (read-only for all)
CREATE POLICY "activity_feed_select" ON activity_feed FOR SELECT TO authenticated USING (true);

-- quest_verifications
CREATE POLICY "quest_verifications_select" ON quest_verifications FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY "quest_verifications_insert" ON quest_verifications FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);

-- ======================== RPC FUNCTIONS ========================

-- Initialize quest user profile
CREATE OR REPLACE FUNCTION initialize_quest_user(p_referral_code text DEFAULT NULL)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_user_id uuid := auth.uid();
  v_email text;
  v_ref_code text;
  v_referrer_id uuid;
  v_existing quest_users;
BEGIN
  IF v_user_id IS NULL THEN
    RAISE EXCEPTION 'Not authenticated';
  END IF;

  -- Check if already exists
  SELECT * INTO v_existing FROM quest_users WHERE id = v_user_id;
  IF v_existing.id IS NOT NULL THEN
    RETURN jsonb_build_object('status', 'exists', 'user', row_to_json(v_existing));
  END IF;

  -- Get email from auth
  SELECT email INTO v_email FROM auth.users WHERE id = v_user_id;

  -- Generate unique referral code
  v_ref_code := 'AW' || upper(substr(md5(v_user_id::text || now()::text), 1, 6));

  -- Insert user
  INSERT INTO quest_users (id, email, display_name, referral_code)
  VALUES (v_user_id, v_email, 'AW' || upper(substr(md5(v_user_id::text), 1, 4)) || '..', v_ref_code);

  -- Process referral
  IF p_referral_code IS NOT NULL AND p_referral_code != '' THEN
    SELECT id INTO v_referrer_id FROM quest_users WHERE referral_code = p_referral_code;
    IF v_referrer_id IS NOT NULL AND v_referrer_id != v_user_id THEN
      INSERT INTO referrals (referrer_id, referred_id, points_awarded)
      VALUES (v_referrer_id, v_user_id, 200)
      ON CONFLICT (referred_id) DO NOTHING;

      -- Award referrer points
      UPDATE quest_users SET total_points = total_points + 200 WHERE id = v_referrer_id;

      -- Update referred_by
      UPDATE quest_users SET referred_by = p_referral_code WHERE id = v_user_id;

      -- Activity feed
      INSERT INTO activity_feed (user_display, action_text, points)
      VALUES (
        (SELECT display_name FROM quest_users WHERE id = v_referrer_id),
        'earned a referral bonus',
        200
      );
    END IF;
  END IF;

  RETURN jsonb_build_object('status', 'created', 'referral_code', v_ref_code);
END;
$$;

-- Start quest attempt (cooldown tracking)
CREATE OR REPLACE FUNCTION start_quest_attempt(p_quest_id text)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_user_id uuid := auth.uid();
  v_quest quest_definitions;
  v_last_attempt timestamptz;
  v_already_completed boolean;
BEGIN
  IF v_user_id IS NULL THEN RAISE EXCEPTION 'Not authenticated'; END IF;

  SELECT * INTO v_quest FROM quest_definitions WHERE id = p_quest_id AND enabled = true;
  IF v_quest.id IS NULL THEN RAISE EXCEPTION 'Quest not found or disabled'; END IF;

  -- Check if already completed (for one_time quests)
  IF v_quest.quest_type = 'one_time' THEN
    SELECT EXISTS(SELECT 1 FROM quest_completions WHERE user_id = v_user_id AND quest_id = p_quest_id)
    INTO v_already_completed;
    IF v_already_completed THEN
      RETURN jsonb_build_object('status', 'already_completed');
    END IF;
  END IF;

  -- Check cooldown from last attempt
  SELECT started_at INTO v_last_attempt
  FROM quest_attempts
  WHERE user_id = v_user_id AND quest_id = p_quest_id
  ORDER BY started_at DESC LIMIT 1;

  IF v_last_attempt IS NOT NULL AND
     EXTRACT(EPOCH FROM (now() - v_last_attempt)) < v_quest.cooldown_seconds THEN
    RETURN jsonb_build_object(
      'status', 'cooldown',
      'remaining', v_quest.cooldown_seconds - EXTRACT(EPOCH FROM (now() - v_last_attempt))::integer
    );
  END IF;

  -- Record attempt
  INSERT INTO quest_attempts (user_id, quest_id) VALUES (v_user_id, p_quest_id);

  RETURN jsonb_build_object(
    'status', 'started',
    'cooldown_seconds', v_quest.cooldown_seconds,
    'started_at', now()
  );
END;
$$;

-- Complete quest
CREATE OR REPLACE FUNCTION complete_quest(p_quest_id text, p_proof_url text DEFAULT NULL, p_proof_data jsonb DEFAULT NULL)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_user_id uuid := auth.uid();
  v_quest quest_definitions;
  v_attempt quest_attempts;
  v_today_count integer;
  v_status text;
  v_prereq text;
  v_prereq_done boolean;
  v_display_name text;
BEGIN
  IF v_user_id IS NULL THEN RAISE EXCEPTION 'Not authenticated'; END IF;

  SELECT * INTO v_quest FROM quest_definitions WHERE id = p_quest_id AND enabled = true;
  IF v_quest.id IS NULL THEN RAISE EXCEPTION 'Quest not found or disabled'; END IF;

  -- Check already completed (one_time)
  IF v_quest.quest_type = 'one_time' THEN
    IF EXISTS(SELECT 1 FROM quest_completions WHERE user_id = v_user_id AND quest_id = p_quest_id) THEN
      RETURN jsonb_build_object('status', 'already_completed');
    END IF;
  END IF;

  -- Rate limit: max 15 completions per day
  SELECT COUNT(*) INTO v_today_count
  FROM quest_completions
  WHERE user_id = v_user_id AND created_at::date = CURRENT_DATE;
  IF v_today_count >= 15 THEN
    RETURN jsonb_build_object('status', 'rate_limited', 'message', 'Max 15 quest completions per day');
  END IF;

  -- Check prerequisites
  IF v_quest.prerequisites IS NOT NULL AND array_length(v_quest.prerequisites, 1) > 0 THEN
    FOREACH v_prereq IN ARRAY v_quest.prerequisites LOOP
      SELECT EXISTS(
        SELECT 1 FROM quest_completions
        WHERE user_id = v_user_id AND quest_id = v_prereq AND status IN ('completed','approved')
      ) INTO v_prereq_done;
      IF NOT v_prereq_done THEN
        RETURN jsonb_build_object('status', 'prerequisite_missing', 'missing', v_prereq);
      END IF;
    END LOOP;
  END IF;

  -- Check cooldown (must have started attempt and waited)
  IF v_quest.cooldown_seconds > 0 THEN
    SELECT * INTO v_attempt
    FROM quest_attempts
    WHERE user_id = v_user_id AND quest_id = p_quest_id
    ORDER BY started_at DESC LIMIT 1;

    IF v_attempt.id IS NULL THEN
      RETURN jsonb_build_object('status', 'no_attempt', 'message', 'Must start attempt first');
    END IF;

    IF EXTRACT(EPOCH FROM (now() - v_attempt.started_at)) < v_quest.cooldown_seconds THEN
      RETURN jsonb_build_object(
        'status', 'cooldown_active',
        'remaining', v_quest.cooldown_seconds - EXTRACT(EPOCH FROM (now() - v_attempt.started_at))::integer
      );
    END IF;
  END IF;

  -- Check proof requirements
  IF v_quest.requires_proof AND (p_proof_url IS NULL OR p_proof_url = '') THEN
    RETURN jsonb_build_object('status', 'proof_required', 'message', 'Proof URL is required for this quest');
  END IF;

  -- Determine status
  v_status := 'completed';
  IF v_quest.requires_review THEN
    v_status := 'pending_review';
  END IF;

  -- Insert completion
  INSERT INTO quest_completions (user_id, quest_id, points_awarded, proof_url, proof_data, status)
  VALUES (v_user_id, p_quest_id, v_quest.points, p_proof_url, p_proof_data, v_status)
  ON CONFLICT (user_id, quest_id) DO NOTHING;

  -- Update points (only if not pending review)
  IF v_status = 'completed' THEN
    UPDATE quest_users SET total_points = total_points + v_quest.points WHERE id = v_user_id;
  END IF;

  -- Activity feed
  SELECT display_name INTO v_display_name FROM quest_users WHERE id = v_user_id;
  INSERT INTO activity_feed (user_display, action_text, points)
  VALUES (
    COALESCE(v_display_name, 'Anonymous'),
    'completed ''' || v_quest.name || '''',
    CASE WHEN v_status = 'completed' THEN v_quest.points ELSE 0 END
  );

  RETURN jsonb_build_object(
    'status', v_status,
    'points', v_quest.points,
    'quest', v_quest.name
  );
END;
$$;

-- Daily check-in
CREATE OR REPLACE FUNCTION daily_checkin()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_user_id uuid := auth.uid();
  v_user quest_users;
  v_streak integer;
  v_base_points integer := 50;
  v_bonus integer := 0;
  v_total integer;
  v_display_name text;
BEGIN
  IF v_user_id IS NULL THEN RAISE EXCEPTION 'Not authenticated'; END IF;

  -- Check if already checked in today
  IF EXISTS(SELECT 1 FROM daily_checkins WHERE user_id = v_user_id AND checkin_date = CURRENT_DATE) THEN
    RETURN jsonb_build_object('status', 'already_checked_in');
  END IF;

  SELECT * INTO v_user FROM quest_users WHERE id = v_user_id;
  IF v_user.id IS NULL THEN RAISE EXCEPTION 'User not initialized'; END IF;

  -- Calculate streak
  IF v_user.last_checkin_date = CURRENT_DATE - 1 THEN
    v_streak := v_user.current_streak + 1;
  ELSE
    v_streak := 1;
  END IF;

  -- Streak bonuses
  IF v_streak = 3 THEN v_bonus := 100;
  ELSIF v_streak = 7 THEN v_bonus := 300;
  ELSIF v_streak = 14 THEN v_bonus := 1000;
  ELSIF v_streak = 30 THEN v_bonus := 3000;
  END IF;

  v_total := v_base_points + v_bonus;

  -- Insert check-in
  INSERT INTO daily_checkins (user_id, checkin_date, points_awarded, streak_count)
  VALUES (v_user_id, CURRENT_DATE, v_total, v_streak);

  -- Update user
  UPDATE quest_users SET
    total_points = total_points + v_total,
    current_streak = v_streak,
    longest_streak = GREATEST(longest_streak, v_streak),
    last_checkin_date = CURRENT_DATE
  WHERE id = v_user_id;

  -- Activity feed
  SELECT display_name INTO v_display_name FROM quest_users WHERE id = v_user_id;
  INSERT INTO activity_feed (user_display, action_text, points)
  VALUES (COALESCE(v_display_name, 'Anonymous'), 'checked in (day ' || v_streak || ')', v_total);

  RETURN jsonb_build_object(
    'status', 'checked_in',
    'streak', v_streak,
    'points', v_total,
    'bonus', v_bonus,
    'bonus_reason', CASE
      WHEN v_streak = 3 THEN '3-day streak bonus!'
      WHEN v_streak = 7 THEN '7-day streak bonus!'
      WHEN v_streak = 14 THEN '14-day streak bonus!'
      WHEN v_streak = 30 THEN '30-day streak bonus!'
      ELSE NULL
    END
  );
END;
$$;

-- Submit quiz (server-side grading)
CREATE OR REPLACE FUNCTION submit_quiz(p_answers jsonb)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_user_id uuid := auth.uid();
  v_score integer := 0;
  v_total integer := 0;
  v_passed boolean;
  v_q record;
  v_answer integer;
  v_points integer := 400;
  v_display_name text;
BEGIN
  IF v_user_id IS NULL THEN RAISE EXCEPTION 'Not authenticated'; END IF;

  -- Check if already passed
  IF EXISTS(SELECT 1 FROM quiz_attempts WHERE user_id = v_user_id AND passed = true) THEN
    RETURN jsonb_build_object('status', 'already_passed');
  END IF;

  -- Grade answers: p_answers is like [{"question_id": 1, "answer": 2}, ...]
  FOR v_q IN SELECT * FROM quiz_questions WHERE enabled = true LOOP
    v_total := v_total + 1;
    SELECT (elem->>'answer')::integer INTO v_answer
    FROM jsonb_array_elements(p_answers) AS elem
    WHERE (elem->>'question_id')::bigint = v_q.id
    LIMIT 1;

    IF v_answer IS NOT NULL AND v_answer = v_q.correct_index THEN
      v_score := v_score + 1;
    END IF;
  END LOOP;

  -- Need 80% to pass (4/5)
  v_passed := (v_total > 0 AND (v_score::float / v_total::float) >= 0.8);

  -- Record attempt
  INSERT INTO quiz_attempts (user_id, answers, score, total, passed)
  VALUES (v_user_id, p_answers, v_score, v_total, v_passed);

  -- Award points if passed
  IF v_passed THEN
    -- Mark quest as completed
    INSERT INTO quest_completions (user_id, quest_id, points_awarded, status)
    VALUES (v_user_id, 'knowledge-quiz', v_points, 'completed')
    ON CONFLICT (user_id, quest_id) DO NOTHING;

    UPDATE quest_users SET total_points = total_points + v_points WHERE id = v_user_id;

    SELECT display_name INTO v_display_name FROM quest_users WHERE id = v_user_id;
    INSERT INTO activity_feed (user_display, action_text, points)
    VALUES (COALESCE(v_display_name, 'Anonymous'), 'aced the Knowledge Quiz (' || v_score || '/' || v_total || ')', v_points);
  END IF;

  RETURN jsonb_build_object(
    'status', CASE WHEN v_passed THEN 'passed' ELSE 'failed' END,
    'score', v_score,
    'total', v_total,
    'points', CASE WHEN v_passed THEN v_points ELSE 0 END
  );
END;
$$;

-- Get leaderboard
CREATE OR REPLACE FUNCTION get_leaderboard(p_limit integer DEFAULT 20)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  RETURN (
    SELECT jsonb_agg(row_to_json(t))
    FROM (
      SELECT display_name, total_points, current_streak,
        CASE
          WHEN total_points >= 5000 THEN 'DIAMOND'
          WHEN total_points >= 3000 THEN 'GOLD'
          WHEN total_points >= 1500 THEN 'SILVER'
          WHEN total_points >= 500 THEN 'BRONZE'
          ELSE 'RECRUIT'
        END AS tier,
        ROW_NUMBER() OVER (ORDER BY total_points DESC) AS rank
      FROM quest_users
      ORDER BY total_points DESC
      LIMIT p_limit
    ) t
  );
END;
$$;

-- Get community stats
CREATE OR REPLACE FUNCTION get_community_stats()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  RETURN jsonb_build_object(
    'total_users', (SELECT COUNT(*) FROM quest_users),
    'total_points', (SELECT COALESCE(SUM(total_points), 0) FROM quest_users),
    'total_completions', (SELECT COUNT(*) FROM quest_completions WHERE status IN ('completed','approved')),
    'total_checkins', (SELECT COUNT(*) FROM daily_checkins)
  );
END;
$$;

-- Get user profile
CREATE OR REPLACE FUNCTION get_user_profile()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_user_id uuid := auth.uid();
  v_user quest_users;
  v_completions jsonb;
  v_achievements jsonb;
  v_referral_count integer;
  v_rank integer;
BEGIN
  IF v_user_id IS NULL THEN RAISE EXCEPTION 'Not authenticated'; END IF;

  SELECT * INTO v_user FROM quest_users WHERE id = v_user_id;
  IF v_user.id IS NULL THEN RAISE EXCEPTION 'User not initialized'; END IF;

  SELECT jsonb_agg(jsonb_build_object('quest_id', quest_id, 'status', status, 'points', points_awarded, 'created_at', created_at))
  INTO v_completions
  FROM quest_completions WHERE user_id = v_user_id;

  SELECT jsonb_agg(jsonb_build_object('achievement_id', achievement_id, 'unlocked_at', unlocked_at))
  INTO v_achievements
  FROM user_achievements WHERE user_id = v_user_id;

  SELECT COUNT(*) INTO v_referral_count FROM referrals WHERE referrer_id = v_user_id;

  SELECT COUNT(*) + 1 INTO v_rank
  FROM quest_users WHERE total_points > v_user.total_points;

  RETURN jsonb_build_object(
    'id', v_user.id,
    'email', v_user.email,
    'display_name', v_user.display_name,
    'total_points', v_user.total_points,
    'current_streak', v_user.current_streak,
    'longest_streak', v_user.longest_streak,
    'last_checkin_date', v_user.last_checkin_date,
    'referral_code', v_user.referral_code,
    'referral_count', v_referral_count,
    'rank', v_rank,
    'completions', COALESCE(v_completions, '[]'::jsonb),
    'achievements', COALESCE(v_achievements, '[]'::jsonb)
  );
END;
$$;

-- Get activity feed
CREATE OR REPLACE FUNCTION get_activity_feed(p_limit integer DEFAULT 20)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  RETURN (
    SELECT jsonb_agg(row_to_json(t))
    FROM (
      SELECT user_display, action_text, points, created_at
      FROM activity_feed
      ORDER BY created_at DESC
      LIMIT p_limit
    ) t
  );
END;
$$;

-- ======================== ENABLE REALTIME ========================

ALTER PUBLICATION supabase_realtime ADD TABLE activity_feed;

-- ======================== SEED DATA: QUIZ QUESTIONS ========================

INSERT INTO quiz_questions (question, options, correct_index, enabled) VALUES
('What blockchain does AgentWallet primarily operate on?',
 '["Ethereum", "Solana", "Polygon", "Avalanche"]', 1, true),

('What protocol does AgentWallet use for HTTP-based payments?',
 '["x401", "x402", "x500", "HTTP-PAY"]', 1, true),

('How many MCP tools does AgentWallet expose?',
 '["12", "27", "42", "53"]', 1, true),

('What mechanism does AgentWallet use for trustless agent-to-agent payments?',
 '["Direct transfer", "Escrow", "Payment channels", "Bridges"]', 1, true),

('What is the purpose of spending policies in AgentWallet?',
 '["Track analytics", "Constrain agent transactions", "Generate reports", "Manage users"]', 1, true),

('Which SDK language does AgentWallet officially support?',
 '["JavaScript", "Rust", "Python", "Go"]', 2, true),

('What does MCP stand for in the AgentWallet context?',
 '["Multi-Chain Protocol", "Model Context Protocol", "Managed Crypto Payments", "Modular Contract Platform"]', 1, true),

('What happens when an escrow is disputed in AgentWallet?',
 '["Funds are burned", "Funds are split 50/50", "It enters DISPUTED state for resolution", "Funds auto-refund"]', 2, true),

('How many API endpoints does AgentWallet v0.2.0 have?',
 '["27", "42", "53", "64"]', 2, true),

('What type of wallet is auto-provisioned when you create an agent?',
 '["EVM wallet", "Bitcoin wallet", "Solana wallet", "Multi-chain wallet"]', 2, true),

('What compliance feature does AgentWallet include?',
 '["KYC verification", "Audit logging", "Tax reporting", "Identity proofing"]', 1, true),

('What is the role of webhooks in AgentWallet?',
 '["User authentication", "Real-time event notifications", "Data backup", "Load balancing"]', 1, true),

('Which policy rule type limits maximum SOL per transaction?',
 '["daily_limit", "rate_limit", "max_transaction_amount", "whitelist"]', 2, true),

('What does the AgentWallet marketplace allow?',
 '["NFT trading", "Agent services hiring", "Token swaps", "Lending"]', 1, true),

('How does AgentWallet handle anomaly detection?',
 '["Manual review only", "Automated compliance engine flagging", "Third-party service", "No anomaly detection"]', 1, true);

-- ======================== SEED DATA: QUEST DEFINITIONS ========================

INSERT INTO quest_definitions (id, name, description, category, points, quest_type, prerequisites, cooldown_seconds, requires_proof, requires_review, enabled) VALUES
('follow-twitter', 'Follow @Web3__Youth', 'Follow the official AgentWallet builder on X', 'social', 200, 'one_time', '{}', 30, false, false, true),
('follow-aw', 'Follow @agentwallet_pro', 'Follow the official AgentWallet protocol account', 'social', 200, 'one_time', '{follow-twitter}', 30, false, false, true),
('tweet-about', 'Tweet About AgentWallet', 'Share your excitement about the protocol with a tweet', 'social', 500, 'one_time', '{follow-twitter,follow-aw}', 45, true, true, true),
('like-retweet', 'Like & Retweet Pinned Post', 'Engage with our latest announcement tweet', 'social', 300, 'one_time', '{follow-twitter}', 30, false, false, true),
('thread', 'Write a Thread (3+ tweets)', 'Write a thread explaining AgentWallet. Mention @agentwallet_pro.', 'social', 1000, 'one_time', '{follow-twitter,follow-aw,tweet-about}', 60, true, true, true),
('join-whitelist', 'Join Mainnet Whitelist', 'Register your Solana wallet for the mainnet beta', 'community', 300, 'one_time', '{}', 0, false, false, true),
('star-github', 'Star GitHub Repository', 'Star the open-source AgentWallet repo on GitHub', 'community', 400, 'one_time', '{}', 45, false, false, true),
('try-dashboard', 'Try the Dashboard', 'Register and create your first agent on the live dashboard', 'community', 500, 'one_time', '{}', 0, false, false, true),
('read-docs', 'Read the API Docs', 'Explore the full API documentation (75%+ scroll, 60s+ time)', 'builder', 200, 'one_time', '{}', 0, false, false, true),
('install-sdk', 'Install the Python SDK', 'Run pip install aw-protocol-sdk and paste pip show output', 'builder', 500, 'one_time', '{read-docs}', 0, true, false, true),
('knowledge-quiz', 'Knowledge Quiz', 'Answer 5 random questions about AgentWallet (80% pass rate)', 'builder', 400, 'one_time', '{read-docs}', 0, false, false, true),
('daily-checkin', 'Daily Check-in', 'Check in daily to earn points and build streaks', 'daily', 50, 'daily', '{}', 0, false, false, true),
('typing-challenge', 'Speed Typing Challenge', 'Type a paragraph about AgentWallet accurately and quickly', 'community', 300, 'one_time', '{}', 0, false, false, true),
('content-creation', 'Content Creation', 'Create a blog post or video about AgentWallet and submit URL', 'social', 750, 'one_time', '{tweet-about}', 0, true, true, true);
