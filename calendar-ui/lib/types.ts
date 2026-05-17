export interface Announcement {
  id: string
  title: string
  startDateTime: string | null
  deadlineDateTime: string | null
  summary: string
  originalUrl: string
  channelName: string
  category: Category
  createdAt: string
}

export type Category =
  | "공지사항"
  | "과목평가"
  | "취업지원"
  | "행사/이벤트"
  | "프로젝트"

export interface CategoryConfig {
  id: Category
  label: string
  color: string
  bgColor: string
  textColor: string
  borderColor: string
}