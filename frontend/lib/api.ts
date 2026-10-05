import type { DebateLevel, DebateSide } from './motions'

export const USE_MOCK = false
export const BASE_URL = 'http://localhost:8000'

export type DebatePayload = { motion: string; student_side: DebateSide; level: DebateLevel; speech: string }
export type DebateResult = {
  rebuttal: string
  feedback: {
    scores: { content: number; style: number; strategy: number }
    strengths: string[]
    weaknesses: string[]
    quotes: { from_student: string; comment: string }[]
    next_drill: string
    overall_comment: string
  }
}

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export async function transcribeAudio(blob: Blob): Promise<{ text: string }> {
  if (USE_MOCK) { await wait(1500); return { text: 'My main argument is that this change would give students more time to rest and learn well. A later start could improve focus, attendance, and the energy we bring into the classroom.' } }
  const form = new FormData(); form.append('audio', blob)
  const response = await fetch(`${BASE_URL}/transcribe`, { method: 'POST', body: form })
  if (!response.ok) throw new Error('Transcription failed')
  return response.json()
}

export async function submitSpeech(payload: DebatePayload): Promise<DebateResult> {
  if (USE_MOCK) {
    await wait(1500)
    const supports = payload.student_side === 'Proposition'
    return { rebuttal: supports ? 'A later start sounds helpful, but it could create real problems for families. Parents may still need to leave for work early, transport schedules could become harder to coordinate, and a shorter afternoon could reduce time for clubs and sport. A strong proposal would need to explain how schools can support those students.' : 'Starting later may create challenges, but the benefits deserve attention. Better-rested students may focus more effectively, and schools could adjust transport or activities with careful planning. The key question is whether the improvements in learning and wellbeing outweigh the changes to family routines.', feedback: { scores: { content: 8, style: 7, strategy: 8 }, strengths: ['You made your position clear early.', 'Your reasoning connected the motion to student wellbeing.', 'The speech was focused and easy to follow.'], weaknesses: ['Add a specific example or piece of evidence.', 'Address the strongest opposing concern directly.'], quotes: [{ from_student: 'A later start could improve focus, attendance, and the energy we bring into the classroom.', comment: 'This is a clear chain of reasoning. Add a real-world example to make it more convincing.' }, { from_student: 'My main argument is that this change would give students more time to rest and learn well.', comment: 'A strong opening. You could preview your second argument so the judge knows where you are going.' }], next_drill: 'Give a 30-second rebuttal to the concern that a later start would make childcare and transport harder.', overall_comment: 'This was a confident mini speech with a clear line of argument. Next, practise weighing your benefits against the opposition’s best practical objection.' } }
  }
  const response = await fetch(`${BASE_URL}/debate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!response.ok) throw new Error('Debate request failed')
  return response.json()
}
