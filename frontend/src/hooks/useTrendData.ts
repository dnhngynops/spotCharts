import { useQuery } from '@tanstack/react-query'
import { supabase } from '../lib/supabaseClient'
import type { TrendInfo } from '../lib/types'

/**
 * Returns the Friday ISO date ("YYYY-MM-DD") for the chart week that contains
 * the given date. Spotify chart weeks run Friday → Thursday.
 *  getDay(): 0=Sun 1=Mon 2=Tue 3=Wed 4=Thu 5=Fri 6=Sat
 *  daysSinceFriday: Fri=0 Sat=1 Sun=2 Mon=3 Tue=4 Wed=5 Thu=6
 */
function chartWeekKey(dateStr: string): string {
  const d = new Date(dateStr)
  const daysSinceFriday = (d.getDay() + 2) % 7
  const friday = new Date(d)
  friday.setDate(d.getDate() - daysSinceFriday)
  return friday.toISOString().slice(0, 10)
}

async function fetchTrendData(
  currentRunId: string,
  trackIds: string[]
): Promise<Map<string, TrendInfo>> {
  const result = new Map<string, TrendInfo>()
  if (!trackIds.length) return result

  // 1. Find the current scrape by matching run_id in notes
  const { data: runs, error: runsErr } = await supabase
    .from('playlist_scrapes')
    .select('scrape_id, scrape_date, notes')
    .eq('status', 'completed')
    .eq('scrape_type', 'scheduled')
    .order('scrape_date', { ascending: true })

  if (runsErr || !runs || runs.length === 0) return result

  const scheduledScrapeIds = runs.map(r => r.scrape_id)

  // 2. Resolve Spotify track IDs → internal song_ids
  const { data: songRows, error: songErr } = await supabase
    .from('songs')
    .select('song_id, spotify_id')
    .in('spotify_id', trackIds)

  if (songErr || !songRows || songRows.length === 0) return result

  const songIdToTrackId: Record<number, string> = {}
  const songIds = songRows.map(s => {
    songIdToTrackId[s.song_id] = s.spotify_id
    return s.song_id
  })

  // 3. Fetch position history + scrape dates — only from scheduled chart runs,
  //    not manual single-playlist ingestions which would corrupt trend deltas.
  const { data: history, error: histErr } = await supabase
    .from('playlist_songs')
    .select('scrape_id, song_id, position, playlist_scrapes(scrape_date)')
    .in('song_id', songIds)
    .in('scrape_id', scheduledScrapeIds)

  if (histErr || !history) return result

  // 4. Group by trackId, deduplicate into chart weeks, compute trend
  const trackEntries: Record<string, { scrape_id: number; position: number; scrape_date: string | null }[]> = {}
  history.forEach(e => {
    const trackId = songIdToTrackId[e.song_id]
    if (!trackId) return
    if (!trackEntries[trackId]) trackEntries[trackId] = []
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const scrapeDate = (e.playlist_scrapes as any)?.scrape_date ?? null
    trackEntries[trackId].push({
      scrape_id: e.scrape_id,
      position: e.position,
      scrape_date: scrapeDate,
    })
  })

  for (const [trackId, entries] of Object.entries(trackEntries)) {
    // Collapse by chart week (most recent scrape per week)
    const weekMap: Record<string, typeof entries[0]> = {}
    entries.forEach(e => {
      const wk = e.scrape_date ? chartWeekKey(e.scrape_date) : String(e.scrape_id)
      if (!weekMap[wk] || e.scrape_id > weekMap[wk].scrape_id) {
        weekMap[wk] = e
      }
    })

    const weekEntries = Object.values(weekMap).sort((a, b) => a.scrape_id - b.scrape_id)
    const weeksOnChart = weekEntries.length
    const peakPos = Math.min(...weekEntries.map(e => e.position))

    let badge: TrendInfo['badge']
    let delta = 0

    if (weeksOnChart === 1) {
      badge = 'new'
    } else {
      const prev = weekEntries[weekEntries.length - 2]
      const curr = weekEntries[weekEntries.length - 1]
      delta = prev.position - curr.position // positive = moved up
      if (delta > 0) badge = 'up'
      else if (delta < 0) badge = 'down'
      else badge = 'same'
    }

    result.set(trackId, { badge, delta: Math.abs(delta), weeksOnChart, peakPos })
  }

  return result
}

/**
 * Bulk-fetches trend badges for all tracks in the current run.
 * Returns a Map<spotifyTrackId, TrendInfo> — empty map until data loads.
 */
export function useTrendData(currentRunId: string, trackIds: string[]) {
  return useQuery<Map<string, TrendInfo>>({
    queryKey: ['trendData', currentRunId],
    queryFn: () => fetchTrendData(currentRunId, trackIds),
    // Don't refetch on window focus — this data only changes weekly
    staleTime: 1000 * 60 * 60,
    enabled: Boolean(currentRunId) && trackIds.length > 0,
    // Return empty map while loading/error so TracksTable renders without badges
    placeholderData: new Map(),
  })
}
