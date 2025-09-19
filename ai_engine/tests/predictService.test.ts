import { predictScore } from '../src/services/predictService';

test('predictScore returns predicted_score', async () => {
  const pred = await predictScore('student-uuid', { featureA: 1 });
  expect(pred).toHaveProperty('predicted_score');
});
