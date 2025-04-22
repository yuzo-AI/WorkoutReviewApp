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

-- 将来的に必要になるかもしれないユーザーテーブル（現状はMVPスコープ外）
-- CREATE TABLE users (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     email TEXT UNIQUE NOT NULL,
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
--     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- );

-- インデックスの作成
CREATE INDEX idx_training_records_date ON training_records(training_date);
CREATE INDEX idx_training_records_exercise ON training_records(exercise_name);  