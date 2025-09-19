import React from 'react';
import { Card, Row, Col, Statistic } from 'antd';
import { useQuery } from 'react-query';
import axios from 'axios';

interface DashboardStats {
  totalExams: number;
  totalQuestions: number;
  totalAssets: number;
  activeUsers: number;
}

const fetchDashboardStats = async (): Promise<DashboardStats> => {
  const { data } = await axios.get('/api/admin/dashboard-stats');
  return data;
};

const DashboardPage: React.FC = () => {
  const { data, error, isLoading } = useQuery('dashboardStats', fetchDashboardStats, {
    refetchInterval: 60000, // Refresh data every 60 seconds
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading dashboard stats</div>;

  return (
    <Row gutter={[16, 16]}>
      <Col span={6}>
        <Card>
          <Statistic title="Total Exams" value={data?.totalExams || 0} />
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic title="Total Questions" value={data?.totalQuestions || 0} />
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic title="Total Assets" value={data?.totalAssets || 0} />
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic title="Active Users" value={data?.activeUsers || 0} />
        </Card>
      </Col>
    </Row>
  );
};

export default DashboardPage;
