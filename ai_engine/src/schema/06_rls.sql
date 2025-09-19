-- Student profile access (students can only see their own data)
CREATE POLICY "Students can view own profile" ON student_profiles
    FOR SELECT TO authenticated
    USING (auth.uid() = auth_user_id);

CREATE POLICY "Students can update own profile" ON student_profiles
    FOR UPDATE TO authenticated
    USING (auth.uid() = auth_user_id)
    WITH CHECK (auth.uid() = auth_user_id);

-- Knowledge states access
CREATE POLICY "Students access own knowledge states" ON student_knowledge_states
    FOR ALL TO authenticated
    USING (
        student_id IN (
            SELECT id FROM student_profiles
            WHERE auth_user_id = auth.uid()
        )
    );

-- Learning sessions access
CREATE POLICY "Students access own sessions" ON learning_sessions
    FOR ALL TO authenticated
    USING (
        student_id IN (
            SELECT id FROM student_profiles
            WHERE auth_user_id = auth.uid()
        )
    );

-- Question interactions access
CREATE POLICY "Students access own interactions" ON question_interactions
    FOR ALL TO authenticated
    USING (
        student_id IN (
            SELECT id FROM student_profiles
            WHERE auth_user_id = auth.uid()
        )
    );

-- AI recommendations access
CREATE POLICY "Students access own recommendations" ON ai_recommendations
    FOR SELECT TO authenticated
    USING (
        student_id IN (
            SELECT id FROM student_profiles
            WHERE auth_user_id = auth.uid()
        )
    );

-- AI predictions access (read-only for students)
CREATE POLICY "Students view own predictions" ON ai_predictions
    FOR SELECT TO authenticated
    USING (
        student_id IN (
            SELECT id FROM student_profiles
            WHERE auth_user_id = auth.uid()
        )
    );
