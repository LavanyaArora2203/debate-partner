export type DebateLevel = 'beginner' | 'intermediate' | 'advanced'

export type Motion = {
  id: string
  text: string
  level: DebateLevel
}

export const motions: Motion[] = [
  { id: 'school-uniforms', text: 'Schools should require students to wear uniforms.', level: 'beginner' },
  { id: 'homework', text: 'Schools should replace homework with independent reading.', level: 'beginner' },
  { id: 'school-day', text: 'The school day should start later.', level: 'beginner' },
  { id: 'social-media', text: 'Social media does more harm than good for teenagers.', level: 'intermediate' },
  { id: 'public-transport', text: 'Public transport should be free for everyone.', level: 'intermediate' },
  { id: 'ai-classroom', text: 'Students should be allowed to use AI tools in class.', level: 'intermediate' },
  { id: 'voting-age', text: 'The voting age should be lowered to sixteen.', level: 'advanced' },
  { id: 'four-day-week', text: 'A four-day school week would improve education.', level: 'advanced' },
]

export const levelLabels: Record<DebateLevel, string> = {
  beginner: 'Beginner',
  intermediate: 'Intermediate',
  advanced: 'Advanced',
}

export const levelStyles: Record<DebateLevel, string> = {
  beginner: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300',
  intermediate: 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300',
  advanced: 'bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-300',
}

export const levelToApi: Record<string, DebateLevel> = {
  Beginner: 'beginner',
  Intermediate: 'intermediate',
  Advanced: 'advanced',
}

export const displayLevel: Record<DebateLevel, DisplayLevel> = {
  beginner: 'Beginner',
  intermediate: 'Intermediate',
  advanced: 'Advanced',
}

export const sampleLevels = ['Beginner', 'Intermediate', 'Advanced'] as const
export type DisplayLevel = (typeof sampleLevels)[number]

export function wordCount(text: string) {
  return text.trim() ? text.trim().split(/\s+/).length : 0
}

export function formatTime(seconds: number) {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, '0')
  const remainder = (seconds % 60).toString().padStart(2, '0')
  return `${minutes}:${remainder}`
}

export function getMotion(id: string) {
  return motions.find((motion) => motion.id === id)
}

export function getRandomMotion(currentId?: string) {
  const available = motions.filter((motion) => motion.id !== currentId)
  return available[Math.floor(Math.random() * available.length)] ?? motions[0]
}

export function getMotionsByLevel(level: DisplayLevel) {
  return motions.filter((motion) => motion.level === level.toLowerCase())
}

export function motionLevelLabel(level: DebateLevel) {
  return displayLevel[level]
}

export function sideDescription(side: 'Proposition' | 'Opposition') {
  return side === 'Proposition' ? 'Support the motion' : 'Argue against the motion'
}

export function sideOpponent(side: 'Proposition' | 'Opposition') {
  return side === 'Proposition' ? 'Opposition' : 'Proposition'
}

export function sideLabel(side: 'Proposition' | 'Opposition') {
  return side === 'Proposition' ? 'Proposition' : 'Opposition'
}

export function levelFromMotion(motion: Motion) {
  return displayLevel[motion.level]
}

export function getMotionLabel(id: string) {
  return getMotion(id)?.text ?? ''
}

export function levelBadgeClass(level: DebateLevel) {
  return levelStyles[level]
}

export function levelFromDisplay(level: DisplayLevel): DebateLevel {
  return level.toLowerCase() as DebateLevel
}

export const sideOptions = [
  { value: 'Proposition' as const, label: 'Proposition', description: 'Support the motion' },
  { value: 'Opposition' as const, label: 'Opposition', description: 'Argue against the motion' },
]

export type DebateSide = (typeof sideOptions)[number]['value']

export const levels = sampleLevels

export function getLevelMotionCount(level: DisplayLevel) {
  return getMotionsByLevel(level).length
}

export function getMotionByText(text: string) {
  return motions.find((motion) => motion.text === text)
}

export function getLevelForMotion(text: string): DisplayLevel {
  return motionLevelLabel(getMotionByText(text)?.level ?? 'beginner') as DisplayLevel
}

export function getMotionOptions(level: DisplayLevel) {
  return getMotionsByLevel(level)
}

export function displayToApiLevel(level: DisplayLevel): DebateLevel {
  return levelFromDisplay(level)
}

export function apiToDisplayLevel(level: DebateLevel): DisplayLevel {
  return displayLevel[level]
}

export function isDebateSide(value: string): value is DebateSide {
  return value === 'Proposition' || value === 'Opposition'
}

export function isDisplayLevel(value: string): value is DisplayLevel {
  return sampleLevels.includes(value as DisplayLevel)
}

export function getDefaultMotion() {
  return motions[0]
}

export function getDefaultLevel(): DisplayLevel {
  return 'Beginner'
}

export function getLevelBadge(level: DebateLevel) {
  return { label: displayLevel[level], className: levelStyles[level] }
}

export function randomMotionId() {
  return getRandomMotion()?.id ?? motions[0].id
}

export function selectMotionForLevel(level: DisplayLevel, currentId?: string) {
  const list = getMotionsByLevel(level)
  return list.find((motion) => motion.id !== currentId) ?? list[0] ?? motions[0]
}

export function normalizeLevel(level: string): DebateLevel {
  return level.toLowerCase() as DebateLevel
}

export function normalizeSide(side: string): DebateSide {
  return isDebateSide(side) ? side : 'Proposition'
}

export function wordCountLabel(count: number) {
  return `${count} ${count === 1 ? 'word' : 'words'}`
}

export function isNearWordLimit(count: number) {
  return count >= 540
}

export function isSpeechLongEnough(count: number) {
  return count >= 30
}

export function createMotionQuote(motion: Motion) {
  return `"${motion.text}"`
}

export const motionGroups = sampleLevels.map((level) => ({ level, motions: getMotionsByLevel(level) }))

export default motions

export function getLevelDescription(level: DisplayLevel) {
  return level === 'Beginner' ? 'Build your confidence' : level === 'Intermediate' ? 'Sharpen your case' : 'Challenge yourself'
}

export function sideAccent(side: DebateSide) {
  return side === 'Proposition' ? 'bg-primary/10 text-primary' : 'bg-secondary text-secondary-foreground'
}

export function randomMotionForLevel(level: DisplayLevel) {
  const list = getMotionsByLevel(level)
  return list[Math.floor(Math.random() * list.length)] ?? motions[0]
}

export function motionSummary(motion?: Motion) {
  return motion ? `${displayLevel[motion.level]} motion` : 'Choose a motion'
}

export function getOtherSide(side: DebateSide) {
  return sideOpponent(side)
}

export function getSelectedMotion(id?: string) {
  return id ? getMotion(id) : undefined
}

export function getMotionCount() {
  return motions.length
}

export function getAllLevels() {
  return sampleLevels
}

export function getMotionIds() {
  return motions.map((motion) => motion.id)
}

export function isLevel(value: string): value is DebateLevel {
  return ['beginner', 'intermediate', 'advanced'].includes(value)
}

export function isWithinWordLimit(count: number) {
  return count <= 600
}

export function getMotionLevel(id: string): DebateLevel {
  return getMotion(id)?.level ?? 'beginner'
}

export function getMotionBadge(id: string) {
  return getLevelBadge(getMotionLevel(id))
}

export function chooseFirstMotion() {
  return motions[0]
}

export function getOpposingSide(side: DebateSide): DebateSide {
  return side === 'Proposition' ? 'Opposition' : 'Proposition'
}

export function getRandomMotionText(currentId?: string) {
  return getRandomMotion(currentId).text
}

export function getMotionLevelLabel(id: string) {
  return displayLevel[getMotionLevel(id)]
}

export function getLevelColor(level: DebateLevel) {
  return levelStyles[level]
}

export function getSelectedSideLabel(side?: DebateSide) {
  return side ?? 'Choose a side'
}

export function isValidMotionId(id: string) {
  return motions.some((motion) => motion.id === id)
}

export function getMotionById(id: string) {
  return getMotion(id)
}

export function getDefaultMotionId() {
  return motions[0].id
}

export function getDefaultSide(): DebateSide {
  return 'Proposition'
}

export function getDefaultLevelForMotion(id: string): DisplayLevel {
  return apiToDisplayLevel(getMotionLevel(id))
}

export function getMotionText(id: string) {
  return getMotion(id)?.text ?? ''
}

export function getMotionLevelClass(id: string) {
  return getLevelColor(getMotionLevel(id))
}

export function getMotionOptionsForDisplay(level: DisplayLevel) {
  return getMotionOptions(level)
}

export function getLevelLabel(level: DebateLevel) {
  return displayLevel[level]
}

export function getDisplayLevel(level: string): DisplayLevel {
  return isDisplayLevel(level) ? level : 'Beginner'
}

export function getLevelFromMotionId(id: string): DisplayLevel {
  return getDefaultLevelForMotion(id)
}

export function getMotionForLevel(level: DisplayLevel) {
  return selectMotionForLevel(level)
}

export function getRandomMotionForCurrent(currentId?: string) {
  return getRandomMotion(currentId)
}

export function getSpeechWordCount(text: string) {
  return wordCount(text)
}

export function getWordLimitMessage(count: number) {
  return `${count}/600 words`
}

export function getSpeechValidationMessage(motionId: string, side: DebateSide | undefined, speech: string) {
  if (!motionId) return 'Choose a motion to continue.'
  if (!side) return 'Choose a side to continue.'
  if (wordCount(speech) < 30) return 'Write at least 30 words to submit.'
  return ''
}