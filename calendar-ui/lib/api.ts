import type { Announcement } from "./types"

// API 기본 URL - 환경변수 또는 기본값 사용
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

// API 엔드포인트
export const API_ENDPOINTS = {
  announcements: `${API_BASE_URL}/announcements/`,
} as const

// API 응답 타입
export interface ApiResponse<T> {
  data: T
  success: boolean
  message?: string
}

// 공지사항 목록 조회
export async function fetchAnnouncements(): Promise<Announcement[]> {
  const response = await fetch(API_ENDPOINTS.announcements, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })

  if (!response.ok) {
    throw new Error(`API 요청 실패: ${response.status} ${response.statusText}`)
  }

  const data = await response.json()

  // 백엔드 응답 형식에 따라 조정 필요
  // 예: { results: [...] } 또는 [...] 형태
  return Array.isArray(data) ? data : data.results || data.data || []
}

// SWR fetcher 함수
export const fetcher = async (url: string) => {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
    },
  })

  if (!response.ok) {
    throw new Error(`API 요청 실패: ${response.status}`)
  }

  const data = await response.json()
  return Array.isArray(data) ? data : data.results || data.data || []
}
