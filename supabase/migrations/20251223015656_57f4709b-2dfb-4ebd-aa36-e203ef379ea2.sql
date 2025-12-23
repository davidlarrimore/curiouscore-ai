-- Create enum for roles
CREATE TYPE public.app_role AS ENUM ('admin', 'user');

-- Create enum for badge types
CREATE TYPE public.badge_type AS ENUM ('milestone', 'category_mastery', 'streak', 'achievement');

-- Create enum for difficulty levels
CREATE TYPE public.difficulty_level AS ENUM ('beginner', 'intermediate', 'advanced', 'expert');

-- Create profiles table
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT UNIQUE,
  avatar_url TEXT,
  xp INTEGER NOT NULL DEFAULT 0,
  level INTEGER NOT NULL DEFAULT 1,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create user_roles table (separate from profiles for security)
CREATE TABLE public.user_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role app_role NOT NULL DEFAULT 'user',
  UNIQUE (user_id, role)
);

-- Create badges table
CREATE TABLE public.badges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  icon TEXT NOT NULL,
  badge_type badge_type NOT NULL,
  xp_reward INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create user_badges table (junction table)
CREATE TABLE public.user_badges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  badge_id UUID NOT NULL REFERENCES public.badges(id) ON DELETE CASCADE,
  earned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE (user_id, badge_id)
);

-- Create challenges table
CREATE TABLE public.challenges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  tags TEXT[] NOT NULL DEFAULT '{}',
  difficulty difficulty_level NOT NULL DEFAULT 'beginner',
  system_prompt TEXT NOT NULL,
  estimated_time_minutes INTEGER NOT NULL DEFAULT 30,
  xp_reward INTEGER NOT NULL DEFAULT 100,
  passing_score INTEGER NOT NULL DEFAULT 70,
  help_resources JSONB DEFAULT '[]',
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create user_progress table
CREATE TABLE public.user_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  challenge_id UUID NOT NULL REFERENCES public.challenges(id) ON DELETE CASCADE,
  progress_percent INTEGER NOT NULL DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
  score INTEGER DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'completed', 'failed')),
  messages JSONB DEFAULT '[]',
  current_phase INTEGER NOT NULL DEFAULT 1,
  mistakes_count INTEGER NOT NULL DEFAULT 0,
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE (user_id, challenge_id)
);

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.badges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_badges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.challenges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_progress ENABLE ROW LEVEL SECURITY;

-- Security definer function to check roles (prevents recursive RLS)
CREATE OR REPLACE FUNCTION public.has_role(_user_id UUID, _role app_role)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM public.user_roles
    WHERE user_id = _user_id
      AND role = _role
  )
$$;

-- Profiles policies
CREATE POLICY "Users can view all profiles"
  ON public.profiles FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can update their own profile"
  ON public.profiles FOR UPDATE
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
  ON public.profiles FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = id);

-- User roles policies (only admins can manage roles)
CREATE POLICY "Users can view their own roles"
  ON public.user_roles FOR SELECT
  TO authenticated
  USING (user_id = auth.uid() OR public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can insert roles"
  ON public.user_roles FOR INSERT
  TO authenticated
  WITH CHECK (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can update roles"
  ON public.user_roles FOR UPDATE
  TO authenticated
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can delete roles"
  ON public.user_roles FOR DELETE
  TO authenticated
  USING (public.has_role(auth.uid(), 'admin'));

-- Badges policies (public read, admin write)
CREATE POLICY "Anyone can view badges"
  ON public.badges FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Admins can manage badges"
  ON public.badges FOR ALL
  TO authenticated
  USING (public.has_role(auth.uid(), 'admin'));

-- User badges policies
CREATE POLICY "Users can view their own badges"
  ON public.user_badges FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "System can insert user badges"
  ON public.user_badges FOR INSERT
  TO authenticated
  WITH CHECK (user_id = auth.uid());

-- Challenges policies (public read, admin write)
CREATE POLICY "Authenticated users can view active challenges"
  ON public.challenges FOR SELECT
  TO authenticated
  USING (is_active = true OR public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can insert challenges"
  ON public.challenges FOR INSERT
  TO authenticated
  WITH CHECK (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can update challenges"
  ON public.challenges FOR UPDATE
  TO authenticated
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can delete challenges"
  ON public.challenges FOR DELETE
  TO authenticated
  USING (public.has_role(auth.uid(), 'admin'));

-- User progress policies
CREATE POLICY "Users can view their own progress"
  ON public.user_progress FOR SELECT
  TO authenticated
  USING (user_id = auth.uid() OR public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Users can insert their own progress"
  ON public.user_progress FOR INSERT
  TO authenticated
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own progress"
  ON public.user_progress FOR UPDATE
  TO authenticated
  USING (user_id = auth.uid());

-- Function to handle new user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, username, avatar_url)
  VALUES (
    NEW.id,
    NEW.raw_user_meta_data ->> 'username',
    NEW.raw_user_meta_data ->> 'avatar_url'
  );
  
  -- Assign default 'user' role
  INSERT INTO public.user_roles (user_id, role)
  VALUES (NEW.id, 'user');
  
  RETURN NEW;
END;
$$;

-- Trigger for new user signup
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to update timestamps
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public;

-- Triggers for updated_at
CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_challenges_updated_at
  BEFORE UPDATE ON public.challenges
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_user_progress_updated_at
  BEFORE UPDATE ON public.user_progress
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

-- Insert default badges
INSERT INTO public.badges (name, description, icon, badge_type, xp_reward) VALUES
  ('First Steps', 'Complete your first challenge', 'trophy', 'milestone', 50),
  ('Quick Learner', 'Complete 5 challenges', 'zap', 'milestone', 100),
  ('AI Explorer', 'Complete 10 challenges', 'compass', 'milestone', 200),
  ('Generative AI Master', 'Complete all Generative AI challenges', 'sparkles', 'category_mastery', 500),
  ('NLP Expert', 'Complete all NLP challenges', 'brain', 'category_mastery', 500),
  ('Prompt Engineer', 'Complete all Prompt Engineering challenges', 'code', 'category_mastery', 500),
  ('Perfect Score', 'Complete a challenge with 100% score', 'star', 'achievement', 150),
  ('Consistent Learner', 'Complete challenges 3 days in a row', 'flame', 'streak', 100);

-- Insert sample challenges
INSERT INTO public.challenges (title, description, tags, difficulty, system_prompt, estimated_time_minutes, xp_reward, passing_score, help_resources) VALUES
  (
    'Introduction to Large Language Models',
    'Learn the fundamentals of LLMs, including transformers, tokenization, and how modern AI models understand and generate text.',
    ARRAY['Generative AI', 'NLP'],
    'beginner',
    'You are an expert AI instructor teaching about Large Language Models. Guide the student through understanding LLMs step by step. Start with basic concepts like what an LLM is, then progress to transformers, attention mechanisms, and tokenization. Ask a mix of multiple choice and open-ended questions. Evaluate responses and provide constructive feedback. Track their understanding and adapt difficulty. Mark phases: 1=What is an LLM, 2=Transformers basics, 3=Attention mechanism, 4=Tokenization, 5=Practical applications. Award points based on answer quality.',
    25,
    150,
    70,
    '[{"title": "Transformer Architecture", "url": "https://arxiv.org/abs/1706.03762", "description": "Original Attention Is All You Need paper"}, {"title": "OpenAI GPT Guide", "url": "https://platform.openai.com/docs", "description": "Official OpenAI documentation"}]'
  ),
  (
    'Prompt Engineering Fundamentals',
    'Master the art of crafting effective prompts to get the best results from AI models.',
    ARRAY['Prompt Engineering', 'Generative AI'],
    'beginner',
    'You are a prompt engineering expert. Teach the student how to write effective prompts. Cover: 1=Basic prompt structure, 2=Context and role setting, 3=Few-shot examples, 4=Chain of thought, 5=Advanced techniques. Use practical examples and have them improve weak prompts. Mix multiple choice with hands-on prompt writing exercises. Evaluate their prompts and give specific improvement suggestions.',
    30,
    175,
    70,
    '[{"title": "OpenAI Prompt Engineering Guide", "url": "https://platform.openai.com/docs/guides/prompt-engineering", "description": "Official best practices for prompting"}, {"title": "Prompt Engineering Patterns", "url": "https://www.promptingguide.ai", "description": "Comprehensive prompting techniques"}]'
  ),
  (
    'Named Entity Recognition with NLP',
    'Understand how NLP models identify and classify named entities in text.',
    ARRAY['NLP', 'AI Ops'],
    'intermediate',
    'You are an NLP specialist teaching Named Entity Recognition. Guide through: 1=What are named entities, 2=Types of entities (PERSON, ORG, LOC, etc.), 3=How NER models work, 4=Evaluation metrics (precision, recall, F1), 5=Real-world applications. Present text examples and ask students to identify entities. Use both MCQ and text analysis questions. Adapt based on their performance.',
    35,
    200,
    75,
    '[{"title": "spaCy NER Guide", "url": "https://spacy.io/usage/linguistic-features#named-entities", "description": "Practical NER with spaCy"}, {"title": "Stanford NER", "url": "https://nlp.stanford.edu/software/CRF-NER.html", "description": "Academic NER resources"}]'
  ),
  (
    'Face Recognition Technology Deep Dive',
    'Explore how facial recognition systems work, their applications, and ethical considerations.',
    ARRAY['Biometrics and FRT'],
    'intermediate',
    'You are a biometrics expert teaching facial recognition technology. Cover: 1=How face detection works, 2=Feature extraction and embeddings, 3=Matching algorithms, 4=Accuracy metrics (FAR, FRR), 5=Ethics and bias considerations. Include both technical MCQ and scenario-based ethical discussions. Adapt complexity based on student responses.',
    40,
    225,
    75,
    '[{"title": "FaceNet Paper", "url": "https://arxiv.org/abs/1503.03832", "description": "Unified embedding for face recognition"}, {"title": "NIST Face Recognition", "url": "https://www.nist.gov/programs-projects/face-recognition-vendor-test-frvt", "description": "NIST evaluation standards"}]'
  ),
  (
    'Building AI Pipelines with MLOps',
    'Learn to design, deploy, and monitor production AI systems using MLOps best practices.',
    ARRAY['AI Ops', 'Generative AI'],
    'advanced',
    'You are an MLOps engineer teaching production AI systems. Cover: 1=ML pipeline fundamentals, 2=Model versioning and registry, 3=CI/CD for ML, 4=Monitoring and observability, 5=Scaling and optimization. Use scenario-based questions about real deployment challenges. Mix architecture decisions (MCQ) with design explanations (text). Be rigorous in evaluating production-readiness of answers.',
    45,
    300,
    80,
    '[{"title": "MLOps Guide", "url": "https://ml-ops.org", "description": "Community MLOps resources"}, {"title": "Google MLOps", "url": "https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning", "description": "Google Cloud MLOps patterns"}]'
  );