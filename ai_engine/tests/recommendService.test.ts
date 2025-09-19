import { getRecommendations } from '../src/services/recommendService';

test('getRecommendations returns array', async () => {
  const recs = await getRecommendations('student-uuid', { mastery: 0.5 });
  expect(Array.isArray(recs)).toBe(true);
});
