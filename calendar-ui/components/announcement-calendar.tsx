"use client"

import { useState, useMemo } from "react"
import useSWR from "swr"
import {
  ChevronLeft,
  ChevronRight,
  Calendar as CalendarIcon,
  Bell,
  ExternalLink,
  ChevronDown,
  Clock,
  Sparkles,
  Megaphone,
  ClipboardList,
  Briefcase,
  PartyPopper,
  FolderKanban,
  RefreshCw,
  Settings2,
  AlertCircle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { cn } from "@/lib/utils"
import { API_ENDPOINTS, fetcher } from "@/lib/api"
import type { Announcement, Category, CategoryConfig } from "@/lib/types"

// 카테고리 설정
const CATEGORIES: CategoryConfig[] = [
  {
    id: "공지사항",
    label: "공지사항",
    color: "bg-blue-500",
    bgColor: "bg-blue-500/10",
    textColor: "text-blue-400",
    borderColor: "border-blue-500/30",
  },
  {
    id: "과목평가",
    label: "과목평가",
    color: "bg-orange-500",
    bgColor: "bg-orange-500/10",
    textColor: "text-orange-400",
    borderColor: "border-orange-500/30",
  },
  {
    id: "취업지원",
    label: "취업지원",
    color: "bg-emerald-500",
    bgColor: "bg-emerald-500/10",
    textColor: "text-emerald-400",
    borderColor: "border-emerald-500/30",
  },
  {
    id: "행사/이벤트",
    label: "행사/이벤트",
    color: "bg-pink-500",
    bgColor: "bg-pink-500/10",
    textColor: "text-pink-400",
    borderColor: "border-pink-500/30",
  },
  {
    id: "프로젝트",
    label: "프로젝트",
    color: "bg-indigo-500",
    bgColor: "bg-indigo-500/10",
    textColor: "text-indigo-400",
    borderColor: "border-indigo-500/30",
  },
]

const CATEGORY_ICONS: Record<Category, React.ElementType> = {
  공지사항: Megaphone,
  과목평가: ClipboardList,
  취업지원: Briefcase,
  "행사/이벤트": PartyPopper,
  프로젝트: FolderKanban,
}

// 폴백용 Mock data (API 실패 시 사용)
const fallbackAnnouncements: Announcement[] = [
  {
    id: "1",
    title: "과목평가 점수 공개",
    startDateTime: "2026-05-19T17:00:00",
    deadlineDateTime: "2026-05-20T09:30:00",
    summary:
      "2026년 1학기 과목평가 점수가 공개됩니다. 마이페이지 > 성적조회에서 확인할 수 있으며, 이의신청은 5/20(수) 09:30까지 가능합니다.",
    originalUrl: "https://meeting.ssafy.com/channel/notice",
    channelName: "공지사항",
    category: "과목평가",
    createdAt: "2026-05-19T10:00:00",
  },
  {
    id: "2",
    title: "설문 마감",
    startDateTime: "2026-05-19T09:00:00",
    deadlineDateTime: "2026-05-19T18:00:00",
    summary:
      "SSAFY 교육 환경 개선을 위한 설문조사가 마감됩니다. 참여자 중 추첨을 통해 소정의 상품을 제공합니다.",
    originalUrl: "https://meeting.ssafy.com/channel/notice",
    channelName: "공지사항",
    category: "행사/이벤트",
    createdAt: "2026-05-18T14:00:00",
  },
  {
    id: "3",
    title: "프로젝트 제출",
    startDateTime: "2026-05-19T10:00:00",
    deadlineDateTime: "2026-05-19T23:59:00",
    summary:
      "2차 프로젝트 결과물 제출 마감일입니다. GitLab에 최종 커밋 후 제출 링크를 등록해주세요.",
    originalUrl: "https://meeting.ssafy.com/channel/project",
    channelName: "프로젝트",
    category: "프로젝트",
    createdAt: "2026-05-17T09:00:00",
  },
  {
    id: "4",
    title: "특강 신청",
    startDateTime: "2026-05-19T19:00:00",
    deadlineDateTime: "2026-05-20T23:59:00",
    summary:
      "개발자 취업 전략 특강 신청이 진행 중입니다. 선착순 마감이므로 빠른 신청을 권장합니다.",
    originalUrl: "https://meeting.ssafy.com/channel/job",
    channelName: "취업지원",
    category: "취업지원",
    createdAt: "2026-05-19T08:00:00",
  },
]

function getDaysInMonth(year: number, month: number) {
  return new Date(year, month + 1, 0).getDate()
}

function getFirstDayOfMonth(year: number, month: number) {
  return new Date(year, month, 1).getDay()
}

function formatDate(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`
}

function parseDate(dateStr: string | null) {
  if (!dateStr) return null
  return new Date(dateStr)
}

function formatDisplayTime(dateStr: string | null) {
  if (!dateStr) return ""
  const date = new Date(dateStr)
  return date.toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
  })
}

function formatDisplayDateTime(dateStr: string | null) {
  if (!dateStr) return ""
  const date = new Date(dateStr)
  return `${date.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })} (${date.getMonth() + 1}/${date.getDate()})`
}

function getCategoryConfig(category: Category): CategoryConfig {
  return CATEGORIES.find((c) => c.id === category) || CATEGORIES[0]
}

function isDeadlineSoon(deadlineDateTime: string | null): boolean {
  if (!deadlineDateTime) return false
  const deadline = new Date(deadlineDateTime)
  const now = new Date()
  const diffHours = (deadline.getTime() - now.getTime()) / (1000 * 60 * 60)
  return diffHours > 0 && diffHours <= 24
}

export default function AnnouncementCalendar() {
  const [currentDate, setCurrentDate] = useState(new Date(2026, 4, 19)) // 2026년 5월 19일
  const [selectedDate, setSelectedDate] = useState<string>("2026-05-19")
  const [expandedAnnouncement, setExpandedAnnouncement] = useState<
    string | null
  >(null)
  const [selectedCategories, setSelectedCategories] = useState<Set<Category>>(
    new Set(CATEGORIES.map((c) => c.id))
  )

  // SWR을 사용한 API 데이터 페칭
  const {
    data: announcements,
    error,
    isLoading,
    mutate,
  } = useSWR<Announcement[]>(API_ENDPOINTS.announcements, fetcher, {
    fallbackData: fallbackAnnouncements,
    revalidateOnFocus: false,
    dedupingInterval: 60000, // 1분간 중복 요청 방지
  })

  const year = currentDate.getFullYear()
  const month = currentDate.getMonth()
  const daysInMonth = getDaysInMonth(year, month)
  const firstDay = getFirstDayOfMonth(year, month)

  const monthNames = [
    "1월",
    "2월",
    "3월",
    "4월",
    "5월",
    "6월",
    "7월",
    "8월",
    "9월",
    "10월",
    "11월",
    "12월",
  ]
  const dayNames = ["일", "월", "화", "수", "목", "금", "토"]

  // 카테고리별 공지 수 계산
  const categoryCounts = useMemo(() => {
    const counts: Record<Category, number> = {
      공지사항: 0,
      과목평가: 0,
      취업지원: 0,
      "행사/이벤트": 0,
      프로젝트: 0,
    }
    ;(announcements || []).forEach((a) => {
      counts[a.category]++
    })
    return counts
  }, [announcements])

  const toggleCategory = (category: Category) => {
    const newSelected = new Set(selectedCategories)
    if (newSelected.has(category)) {
      newSelected.delete(category)
    } else {
      newSelected.add(category)
    }
    setSelectedCategories(newSelected)
  }

  const prevMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1))
  }

  const nextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1))
  }

  const goToToday = () => {
    const today = new Date(2026, 4, 19) // Mock today
    setCurrentDate(today)
    setSelectedDate(formatDate(today))
  }

  // 새로고침 핸들러
  const handleRefresh = () => {
    mutate()
  }

  // 필터링된 공지사항
  const filteredAnnouncements = useMemo(() => {
    return (announcements || []).filter((a) => selectedCategories.has(a.category))
  }, [announcements, selectedCategories])

  // 특정 날짜에 해당하는 공지사항 필터링
  const getAnnouncementsForDate = (dateStr: string) => {
    return filteredAnnouncements.filter((announcement) => {
      const startDate = parseDate(announcement.startDateTime)
      const deadlineDate = parseDate(announcement.deadlineDateTime)

      if (startDate && formatDate(startDate) === dateStr) return true
      if (deadlineDate && formatDate(deadlineDate) === dateStr) return true

      return false
    })
  }

  // 선택된 날짜의 공지사항
  const selectedAnnouncements = selectedDate
    ? getAnnouncementsForDate(selectedDate)
    : []

  // 캘린더 셀 렌더링
  const renderCalendarCells = () => {
    const cells = []
    const totalCells = Math.ceil((firstDay + daysInMonth) / 7) * 7

    // 이전 달 마지막 날들
    const prevMonthDays = getDaysInMonth(year, month - 1)

    for (let i = 0; i < totalCells; i++) {
      const dayNumber = i - firstDay + 1
      const isCurrentMonth = dayNumber > 0 && dayNumber <= daysInMonth

      if (i < firstDay) {
        // 이전 달
        const prevDay = prevMonthDays - firstDay + i + 1
        cells.push(
          <div
            key={`prev-${i}`}
            className="min-h-28 p-2 border-b border-r border-border/30 bg-secondary/20"
          >
            <span className="text-sm text-muted-foreground/50">{prevDay}</span>
          </div>
        )
        continue
      }

      if (dayNumber > daysInMonth) {
        // 다음 달
        const nextDay = dayNumber - daysInMonth
        cells.push(
          <div
            key={`next-${i}`}
            className="min-h-28 p-2 border-b border-r border-border/30 bg-secondary/20"
          >
            <span className="text-sm text-muted-foreground/50">{nextDay}</span>
          </div>
        )
        continue
      }

      const dateStr = formatDate(new Date(year, month, dayNumber))
      const announcements = getAnnouncementsForDate(dateStr)
      const isToday = dateStr === "2026-05-19" // Mock today
      const isSelected = dateStr === selectedDate

      cells.push(
        <button
          type="button"
          key={dateStr}
          onClick={() => setSelectedDate(dateStr)}
          className={cn(
            "min-h-28 p-2 text-left transition-colors border-b border-r border-border/30 hover:bg-secondary/50 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-inset",
            isSelected && "bg-primary/5 ring-2 ring-primary/50 ring-inset"
          )}
        >
          <div className="flex items-start justify-between mb-1">
            <span
              className={cn(
                "text-sm font-medium inline-flex items-center justify-center",
                isToday &&
                  "bg-primary text-primary-foreground rounded-full w-7 h-7",
                !isToday && "text-foreground"
              )}
            >
              {dayNumber}
            </span>
          </div>
          <div className="space-y-1">
            {announcements.slice(0, 3).map((announcement) => {
              const config = getCategoryConfig(announcement.category)
              return (
                <div
                  key={announcement.id}
                  className={cn(
                    "text-xs truncate rounded px-1.5 py-0.5 font-medium",
                    config.bgColor,
                    config.textColor
                  )}
                >
                  {announcement.title}
                </div>
              )
            })}
            {announcements.length > 3 && (
              <div className="text-xs text-muted-foreground pl-1">
                +{announcements.length - 3}개 더
              </div>
            )}
          </div>
        </button>
      )
    }

    return cells
  }

  const selectedDateObj = selectedDate ? new Date(selectedDate) : null

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/50 bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-[1800px] mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-primary/10">
              <CalendarIcon className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">
                SSAFY 공지 캘린더
              </h1>
              <p className="text-xs text-muted-foreground">
                Mattermost 공지 수집 · AI 요약 · 일정 캘린더
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {/* 상태 표시 */}
            {isLoading ? (
              <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-yellow-500/10 text-yellow-400 text-sm">
                <RefreshCw className="w-3 h-3 animate-spin" />
                데이터 로딩 중...
              </div>
            ) : error ? (
              <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-500/10 text-red-400 text-sm">
                <AlertCircle className="w-3 h-3" />
                연결 오류 (폴백 데이터 사용)
              </div>
            ) : (
              <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-400 text-sm">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                실시간 수집 연결됨
              </div>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="rounded-full"
              onClick={handleRefresh}
              disabled={isLoading}
            >
              <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
              <span className="sr-only">새로고침</span>
            </Button>
            <Button variant="ghost" size="icon" className="rounded-full">
              <Bell className="w-4 h-4" />
              <span className="sr-only">알림</span>
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-[1800px] mx-auto p-4 flex gap-4">
        {/* Left Sidebar */}
        <aside className="w-64 shrink-0 space-y-4 hidden lg:block">
          {/* Channel Selection */}
          <Card className="border-border/50 bg-card">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold">
                  채널 선택
                </CardTitle>
                <Button variant="ghost" size="icon" className="h-6 w-6">
                  <Settings2 className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              {CATEGORIES.map((category) => {
                const Icon = CATEGORY_ICONS[category.id]
                const count = categoryCounts[category.id]
                const isChecked = selectedCategories.has(category.id)
                return (
                  <label
                    key={category.id}
                    className="flex items-center gap-3 p-2 rounded-lg hover:bg-secondary/50 cursor-pointer transition-colors"
                  >
                    <Checkbox
                      checked={isChecked}
                      onCheckedChange={() => toggleCategory(category.id)}
                      className={cn(
                        "border-2 data-[state=checked]:border-transparent data-[state=checked]:text-white",
                        isChecked && category.bgColor
                      )}
                      style={{
                        backgroundColor: isChecked
                          ? category.id === "공지사항"
                            ? "#3b82f6"
                            : category.id === "과목평가"
                              ? "#f97316"
                              : category.id === "취업지원"
                                ? "#10b981"
                                : category.id === "행사/이벤트"
                                  ? "#ec4899"
                                  : "#6366f1"
                          : undefined,
                      }}
                    />
                    <div
                      className={cn(
                        "p-1.5 rounded-md",
                        category.bgColor
                      )}
                    >
                      <Icon className={cn("w-4 h-4", category.textColor)} />
                    </div>
                    <span className="flex-1 text-sm font-medium text-foreground">
                      {category.label}
                    </span>
                    <Badge
                      variant="secondary"
                      className="text-xs bg-secondary text-muted-foreground"
                    >
                      {count}
                    </Badge>
                  </label>
                )
              })}
            </CardContent>
          </Card>
        </aside>

        {/* Main Calendar */}
        <main className="flex-1 min-w-0">
          <Card className="border-border/50 bg-card">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={prevMonth}
                    className="h-8 w-8 border-border/50"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    <span className="sr-only">이전 달</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={nextMonth}
                    className="h-8 w-8 border-border/50"
                  >
                    <ChevronRight className="w-4 h-4" />
                    <span className="sr-only">다음 달</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={goToToday}
                    className="border-border/50"
                  >
                    오늘
                  </Button>
                  <h2 className="text-xl font-semibold text-foreground ml-2">
                    {year}년 {monthNames[month]}
                  </h2>
                </div>
                <div className="flex items-center gap-1 bg-secondary rounded-lg p-1">
                  <Button
                    variant="secondary"
                    size="sm"
                    className="bg-card shadow-sm"
                  >
                    월
                  </Button>
                  <Button variant="ghost" size="sm">
                    주
                  </Button>
                  <Button variant="ghost" size="sm">
                    목록
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {/* Day Headers */}
              <div className="grid grid-cols-7 border-b border-border/30">
                {dayNames.map((day, idx) => (
                  <div
                    key={day}
                    className={cn(
                      "py-3 text-center text-sm font-medium border-r border-border/30 last:border-r-0",
                      idx === 0 && "text-red-400",
                      idx === 6 && "text-blue-400",
                      idx !== 0 && idx !== 6 && "text-muted-foreground"
                    )}
                  >
                    {day}
                  </div>
                ))}
              </div>
              {/* Calendar Grid */}
              <div className="grid grid-cols-7">{renderCalendarCells()}</div>
              {/* Legend */}
              <div className="p-4 border-t border-border/30 flex flex-wrap items-center gap-4">
                {CATEGORIES.map((category) => (
                  <div key={category.id} className="flex items-center gap-2">
                    <span
                      className={cn("w-3 h-3 rounded-full", category.color)}
                    />
                    <span className="text-xs text-muted-foreground">
                      {category.label}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          {/* Hint */}
          <p className="text-xs text-muted-foreground mt-3 flex items-center gap-2">
            <span className="text-lg">💡</span>
            날짜를 클릭하면 해당 날짜의 공지 목록을 확인할 수 있습니다.
          </p>
        </main>

        {/* Right Panel - Announcement Details */}
        <aside className="w-80 shrink-0 hidden xl:block">
          <Card className="border-border/50 bg-card sticky top-20">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-semibold">
                  {selectedDateObj
                    ? `${selectedDateObj.getMonth() + 1}월 ${selectedDateObj.getDate()}일 공지`
                    : "날짜를 선택하세요"}
                </CardTitle>
                {selectedAnnouncements.length > 0 && (
                  <Button variant="ghost" size="sm" className="text-primary">
                    전체 보기
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-3 max-h-[calc(100vh-12rem)] overflow-y-auto">
              {!selectedDate ? (
                <p className="text-muted-foreground text-sm text-center py-8">
                  캘린더에서 날짜를 클릭하면
                  <br />
                  해당 날짜의 공지사항을 볼 수 있습니다.
                </p>
              ) : selectedAnnouncements.length === 0 ? (
                <p className="text-muted-foreground text-sm text-center py-8">
                  이 날짜에 등록된 공지사항이 없습니다.
                </p>
              ) : (
                selectedAnnouncements.map((announcement) => (
                  <AnnouncementCard
                    key={announcement.id}
                    announcement={announcement}
                    isExpanded={expandedAnnouncement === announcement.id}
                    onToggle={() =>
                      setExpandedAnnouncement(
                        expandedAnnouncement === announcement.id
                          ? null
                          : announcement.id
                      )
                    }
                  />
                ))
              )}
              {selectedAnnouncements.length > 0 && (
                <Button
                  variant="outline"
                  className="w-full border-dashed border-border/50 text-muted-foreground"
                >
                  + 이 날짜의 공지 추가 요청
                </Button>
              )}
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  )
}

function AnnouncementCard({
  announcement,
  isExpanded,
  onToggle,
}: {
  announcement: Announcement
  isExpanded: boolean
  onToggle: () => void
}) {
  const config = getCategoryConfig(announcement.category)
  const deadlineSoon = isDeadlineSoon(announcement.deadlineDateTime)

  return (
    <Collapsible open={isExpanded} onOpenChange={onToggle}>
      <div className="rounded-lg border border-border/50 bg-card overflow-hidden">
        <CollapsibleTrigger className="w-full p-4 text-left hover:bg-secondary/30 transition-colors">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                <h3 className="font-semibold text-foreground text-sm">
                  {announcement.title}
                </h3>
                <Badge
                  variant="outline"
                  className={cn(
                    "text-xs shrink-0",
                    config.borderColor,
                    config.textColor
                  )}
                >
                  {announcement.category}
                </Badge>
              </div>
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  시작 {formatDisplayTime(announcement.startDateTime)}
                </span>
                {announcement.deadlineDateTime && (
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    마감 {formatDisplayDateTime(announcement.deadlineDateTime)}
                  </span>
                )}
              </div>
              {deadlineSoon && (
                <Badge className="mt-2 bg-red-500/10 text-red-400 border-red-500/30">
                  마감 임박
                </Badge>
              )}
            </div>
            <ChevronDown
              className={cn(
                "w-4 h-4 text-muted-foreground transition-transform shrink-0 mt-1",
                isExpanded && "rotate-180"
              )}
            />
          </div>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="px-4 pb-4 border-t border-border/30 pt-3">
            <div className="flex items-center gap-1.5 text-primary text-xs mb-2">
              <Sparkles className="w-3.5 h-3.5" />
              <span className="font-medium">AI 요약</span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed mb-4">
              {announcement.summary}
            </p>
            <Button
              variant="outline"
              size="sm"
              asChild
              className="w-full gap-1.5"
            >
              <a
                href={announcement.originalUrl}
                target="_blank"
                rel="noopener noreferrer"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                원본 메시지
              </a>
            </Button>
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  )
}
