import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { Bell, Check, CheckCheck, UserPlus, ClipboardCheck, Zap } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ICON_MAP = {
  new_user: UserPlus,
  assessment_completed: ClipboardCheck,
  quick_assessment: Zap,
};

const COLOR_MAP = {
  new_user: "#A78BFA",
  assessment_completed: "#34D399",
  quick_assessment: "#C9A84C",
};

function timeAgo(dateStr) {
  const now = new Date();
  const date = new Date(dateStr);
  const seconds = Math.floor((now - date) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

const NotificationBell = () => {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef(null);

  const fetchUnreadCount = async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/notifications/unread-count`);
      setUnreadCount(res.data.count);
    } catch {
      // silently fail
    }
  };

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${BACKEND_URL}/api/notifications`);
      setNotifications(res.data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  };

  // Poll unread count every 30 seconds
  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  // Load notifications when dropdown opens
  useEffect(() => {
    if (open) fetchNotifications();
  }, [open]);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const markRead = async (id) => {
    try {
      await axios.patch(`${BACKEND_URL}/api/notifications/${id}/read`);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch {
      // silently fail
    }
  };

  const markAllRead = async () => {
    try {
      await axios.post(`${BACKEND_URL}/api/notifications/read-all`);
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch {
      // silently fail
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        data-testid="notification-bell"
        onClick={() => setOpen(!open)}
        className="relative p-2 rounded-xl text-[#4A5568] hover:text-[#0C1B2A] hover:bg-[#F8F9FA] transition-all"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 flex items-center justify-center rounded-full bg-[#EF4444] text-[10px] font-bold text-[#0C1B2A]">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-12 w-80 sm:w-96 glass-heavy rounded-2xl shadow-2xl shadow-black/50 z-[100] overflow-hidden animate-fade-in"
          data-testid="notification-dropdown"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-[#E2E8F0]">
            <h3 className="text-sm font-semibold text-[#0C1B2A] font-['Outfit']">Notifications</h3>
            {unreadCount > 0 && (
              <button
                data-testid="mark-all-read-btn"
                onClick={markAllRead}
                className="flex items-center gap-1 text-xs text-[#C9A84C] hover:text-[#C9A84C]/80 transition-colors"
              >
                <CheckCheck size={14} />
                Mark all read
              </button>
            )}
          </div>

          {/* List */}
          <div className="max-h-80 overflow-y-auto">
            {loading && notifications.length === 0 ? (
              <div className="py-8 text-center text-[#8896A5] text-sm">Loading...</div>
            ) : notifications.length === 0 ? (
              <div className="py-8 text-center text-[#8896A5] text-sm">No notifications yet</div>
            ) : (
              notifications.map((n) => {
                const Icon = ICON_MAP[n.type] || Bell;
                const color = COLOR_MAP[n.type] || "#C9A84C";
                return (
                  <div
                    key={n.id}
                    data-testid={`notification-item-${n.id}`}
                    className={`flex items-start gap-3 px-4 py-3 border-b border-[#E2E8F0] transition-colors cursor-pointer ${
                      n.read ? "opacity-60" : "hover:bg-[#F8F9FA]"
                    }`}
                    onClick={() => !n.read && markRead(n.id)}
                  >
                    <div
                      className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
                      style={{ backgroundColor: `${color}15` }}
                    >
                      <Icon size={16} style={{ color }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-[#0C1B2A] leading-snug">{n.title}</p>
                      <p className="text-[11px] text-[#4A5568] mt-0.5 leading-snug">{n.message}</p>
                      <p className="text-[10px] text-[#8896A5] mt-1">{timeAgo(n.created_at)}</p>
                    </div>
                    {!n.read && (
                      <div className="w-2 h-2 rounded-full bg-[#C9A84C] shrink-0 mt-2" />
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
