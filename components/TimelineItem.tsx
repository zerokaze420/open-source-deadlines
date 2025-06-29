'use client'

import { TimelineEvent } from '@/lib/data'
import { getTimelineStatus } from '@/lib/data'
import { TZDate } from "@date-fns/tz"
import { useState } from 'react'

interface TimelineItemProps {
  event: TimelineEvent
  timezone: string
  isEnded: boolean
  isActive?: boolean
  totalEvents: number
  index: number
}

export function TimelineItem({ event, timezone, isEnded, isActive = false, totalEvents, index }: TimelineItemProps) {
  const [showTooltip, setShowTooltip] = useState(false)
  
  const deadlineDate = new TZDate(event.deadline, timezone)
  
  const status = isEnded ? 'past' : getTimelineStatus(deadlineDate)
  
  // 计算位置百分比，确保不会超出容器边界
  const position = totalEvents > 1 ? (index / (totalEvents - 1)) * 80 + 10 : 50

  return (
    <div 
      className="absolute flex flex-col items-center"
      style={{ 
        left: `${position}%`,
        transform: 'translateX(-50%)',
        top: '50%',
        marginTop: '-6px' // 圆点半径，确保圆点中心对齐到线上
      }}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {/* Tooltip - 向上显示，避免被裁切 */}
      {showTooltip && (
        <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 z-50">
          <div className="bg-gray-900 text-white text-xs rounded-lg px-3 py-2 whitespace-nowrap shadow-lg">
            <div className="font-medium">{event.comment}</div>
            <div className="text-gray-300">
              {deadlineDate.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })} (CST)
            </div>
            <div className="text-gray-300">
              {deadlineDate.toLocaleString('zh-CN', { timeZone: timezone })} ({timezone})
            </div>
            {/* Arrow */}
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
          </div>
        </div>
      )}
      
      {/* Timeline dot */}
      <div className={`w-3 h-3 rounded-full border-2 shadow-sm transition-all duration-300 cursor-pointer ${
        isActive ? 'bg-orange-500 border-orange-300 ring-2 ring-orange-200 scale-125' :
        status === 'current' ? 'bg-orange-500 border-orange-300' :
        status === 'upcoming' ? 'bg-blue-500 border-blue-300' :
        'bg-gray-400 border-gray-300'
      } ${isEnded ? 'opacity-50' : ''} ${showTooltip ? 'scale-125' : ''}`} />
      
      {/* Compact date display - 向下显示 */}
      <div className={`absolute top-full mt-1 text-center transition-all duration-300 ${
        isEnded ? 'opacity-50' : ''
      }`}>
        <div className={`text-xs font-medium whitespace-nowrap ${
          isActive ? 'text-orange-700 font-bold' : 'text-gray-600'
        }`}>
          {deadlineDate.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', month: '2-digit', day: '2-digit' })}
        </div>
      </div>
    </div>
  )
}