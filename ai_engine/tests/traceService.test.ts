import { updateKnowledgeState } from '../src/services/traceService';

test('updateKnowledgeState returns mastery update', async () => {
  const res = await updateKnowledgeState('student-uuid', 'concept-uuid', true);
  expect(res).toHaveProperty('new_mastery');
});
