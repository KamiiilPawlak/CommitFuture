import { Progress } from "@/components/ui/progress"
import type { MatchResultResponse } from "@/lib/api/types"

interface CvMatchOutputProps {
  result?: MatchResultResponse | null
}

function getScoreColorClass(score: number): string {
  if (score >= 75) return "text-chart-2"
  if (score >= 50) return "text-chart-4"
  return "text-destructive"
}

function getProgressColorClass(score: number): string {
  if (score >= 75) return "[&>div]:bg-chart-2"
  if (score >= 50) return "[&>div]:bg-chart-4"
  return "[&>div]:bg-destructive"
}

function StatCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1 border-r border-border px-4 py-3 last:border-r-0">
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="font-mono text-sm tabular-nums">{value}</p>
    </div>
  )
}

function SkillList({ title, skills, empty }: { title: string; skills: string[]; empty: string }) {
  return (
    <div className="flex flex-col gap-2 px-4 py-3">
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
        {title} ({skills.length})
      </p>
      {skills.length > 0 ? (
        <ul className="flex flex-col gap-1">
          {skills.map((skill) => (
            <li key={skill} className="flex items-baseline gap-2 text-sm">
              <span className="text-muted-foreground">–</span>
              <span>{skill}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">{empty}</p>
      )}
    </div>
  )
}

function CvMatchOutput({ result }: CvMatchOutputProps) {
  if (!result) {
    return (
      <section className="mx-auto w-full flex flex-col items-center justify-center gap-2 border border-dashed border-border rounded-md p-8 text-center">
        <p className="text-sm font-medium">Wyniki analizy pojawią się tutaj</p>
        <p className="text-xs text-muted-foreground">
          Wklej ogłoszenie, dodaj CV i rozpocznij matchowanie
        </p>
      </section>
    )
  }

  const score = Math.round(result.overall_score)
  const skillCoverage = Math.round(result.skill_coverage)
  const {
    matched_skills: matchedSkills,
    missing_skills: missingSkills,
    domain_overlap: domainOverlap,
    soft_skill_overlap: softSkillOverlap,
    seniority_match: seniorityMatch,
    education_match: educationMatch,
  } = result

  return (
    <div className="mx-auto w-full flex flex-col gap-4 rounded-md border border-border">
      <div className="flex flex-col gap-2 border-b border-border px-4 py-3">
        <div className="flex items-baseline justify-between">
          <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Wynik ogólny</p>
          <p className={`font-mono text-2xl tabular-nums ${getScoreColorClass(score)}`}>{score}%</p>
        </div>
        <Progress value={score} className={`h-1.5 ${getProgressColorClass(score)}`} />
      </div>

      <div className="grid grid-cols-3 divide-x divide-border border-b border-border">
        <StatCell label="Pokrycie umiejętności" value={`${skillCoverage}%`} />
        <StatCell label="Senioralność" value={seniorityMatch ? "zgodna" : "niezgodna"} />
        <StatCell label="Edukacja" value={educationMatch ? "zgodna" : "niezgodna"} />
      </div>

      <div className="grid grid-cols-1 divide-y divide-border sm:grid-cols-2 sm:divide-y-0 sm:divide-x border-b border-border">
        <SkillList
          title="Umiejętności pokryte"
          skills={matchedSkills}
          empty="Brak dopasowanych umiejętności"
        />
        <SkillList
          title="Umiejętności brakujące"
          skills={missingSkills}
          empty="Brak brakujących umiejętności"
        />
      </div>

      <div className="grid grid-cols-1 divide-y divide-border sm:grid-cols-2 sm:divide-y-0 sm:divide-x">
        <SkillList
          title="Zgodność domenowa"
          skills={domainOverlap}
          empty="Brak zgodności domenowej"
        />
        <SkillList
          title="Umiejętności miękkie"
          skills={softSkillOverlap}
          empty="Brak wspólnych umiejętności miękkich"
        />
      </div>
    </div>
  )
}

export { CvMatchOutput }
