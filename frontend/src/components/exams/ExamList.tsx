import React, { useEffect } from 'react';
import { List, Button } from 'antd';
import { useAppDispatch, useAppSelector } from '../../features/auth/hooks';
import { fetchExams } from '../../features/exams/examSlice';

const ExamListPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { exams, loading, error } = useAppSelector((state) => state.exams);

  useEffect(() => {
    dispatch(fetchExams());
  }, [dispatch]);

  return (
    <div style={{ padding: 24 }}>
      <h2>Exam List</h2>
      {loading && <div>Loading exams...</div>}
      {error && <div style={{ color: 'red' }}>Error: {error}</div>}
      <List
        bordered
        dataSource={exams}
        renderItem={(exam) => (
          <List.Item
            actions={[
              <Button type="link" key="detail" href={`/questions/${exam.id}`}>
                View Questions
              </Button>,
            ]}
          >
            {exam.name}
          </List.Item>
        )}
      />
    </div>
  );
};

export default ExamListPage;
