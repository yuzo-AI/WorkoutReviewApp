-- トレーニング記録テーブル
CREATE TABLE training_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,  -- ユーザーIDを追加
    training_date DATE NOT NULL,
    exercise_name TEXT NOT NULL,
    weight DECIMAL(5,2) NOT NULL,
    reps INTEGER NOT NULL,
    sets INTEGER NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- インデックスの作成
CREATE INDEX idx_training_records_date ON training_records(training_date);
CREATE INDEX idx_training_records_exercise ON training_records(exercise_name);
CREATE INDEX idx_profiles_username ON profiles(username);    