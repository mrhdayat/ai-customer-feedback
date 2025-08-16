import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { 
  Plus, 
  MessageSquare, 
  TrendingUp, 
  Users, 
  Zap,
  BarChart3,
  PieChart,
  Activity
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingState, EmptyState } from '@/components/ui/loading'
import { useAuthStore, isDemo, isMemberOrAdmin } from '@/store/auth'
import { api } from '@/services/api'
import { Project } from '@/types'

export function DashboardPage() {
  const { user } = useAuthStore()
  const [selectedProject, setSelectedProject] = useState<string | null>(null)

  // Get projects
  const { data: projectsData, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.getProjects(),
  })

  // Get project summary for selected project
  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: ['project-summary', selectedProject],
    queryFn: () => selectedProject ? api.getProjectSummary(selectedProject) : null,
    enabled: !!selectedProject,
  })

  const projects = projectsData?.data?.projects || []
  const summary = summaryData?.data

  // Auto-select first project if none selected
  if (!selectedProject && projects.length > 0) {
    setSelectedProject(projects[0].id)
  }

  const stats = [
    {
      title: 'Total Feedbacks',
      value: summary?.total_feedbacks || 0,
      icon: MessageSquare,
      change: '+12%',
      changeType: 'positive' as const
    },
    {
      title: 'Positive Sentiment',
      value: summary?.sentiment_distribution?.positive || 0,
      icon: TrendingUp,
      change: '+5%',
      changeType: 'positive' as const
    },
    {
      title: 'Active Automations',
      value: summary?.automation_stats?.completed || 0,
      icon: Zap,
      change: '+8%',
      changeType: 'positive' as const
    },
    {
      title: 'High Urgency',
      value: summary?.urgency_distribution?.high || 0,
      icon: Activity,
      change: '-3%',
      changeType: 'negative' as const
    }
  ]

  if (projectsLoading) {
    return <LoadingState message="Loading dashboard..." />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Welcome back, {user?.full_name || user?.email}
          </p>
        </div>
        
        {isMemberOrAdmin() && (
          <Button className="flex items-center space-x-2">
            <Plus className="h-4 w-4" />
            <span>New Project</span>
          </Button>
        )}
      </div>

      {/* Project Selector */}
      {projects.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Select Project</CardTitle>
            <CardDescription>
              Choose a project to view its analytics
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((project: Project) => (
                <motion.div
                  key={project.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.2 }}
                >
                  <Card
                    className={`cursor-pointer transition-all hover:shadow-md ${
                      selectedProject === project.id
                        ? 'ring-2 ring-blue-500 border-blue-200'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setSelectedProject(project.id)}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">{project.name}</CardTitle>
                        {project.is_demo && (
                          <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full">
                            Demo
                          </span>
                        )}
                      </div>
                      {project.description && (
                        <CardDescription className="text-sm">
                          {project.description}
                        </CardDescription>
                      )}
                    </CardHeader>
                  </Card>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats Cards */}
      {selectedProject && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          {stats.map((stat) => (
            <Card key={stat.title}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      {stat.title}
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {stat.value.toLocaleString()}
                    </p>
                    <p className={`text-sm mt-1 ${
                      stat.changeType === 'positive' 
                        ? 'text-green-600' 
                        : 'text-red-600'
                    }`}>
                      {stat.change} from last week
                    </p>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-full">
                    <stat.icon className="h-6 w-6 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </motion.div>
      )}

      {/* Charts Section */}
      {selectedProject && summary && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Sentiment Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <PieChart className="h-5 w-5" />
                <span>Sentiment Distribution</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(summary.sentiment_distribution || {}).map(([sentiment, count]) => (
                  <div key={sentiment} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${
                        sentiment === 'positive' ? 'bg-green-500' :
                        sentiment === 'negative' ? 'bg-red-500' : 'bg-gray-500'
                      }`} />
                      <span className="capitalize text-sm font-medium">{sentiment}</span>
                    </div>
                    <span className="text-sm text-gray-600">{count}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Top Topics */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5" />
                <span>Top Topics</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {(summary.top_topics || []).slice(0, 5).map((topic, index) => (
                  <div key={topic.label} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className="text-sm text-gray-500">#{index + 1}</span>
                      <span className="text-sm font-medium capitalize">{topic.label}</span>
                    </div>
                    <span className="text-sm text-gray-600">{topic.count}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Empty State */}
      {projects.length === 0 && (
        <EmptyState
          title="No projects found"
          description={
            isDemo() 
              ? "Demo data is being loaded. Please refresh the page."
              : "Create your first project to start analyzing customer feedback."
          }
          action={
            isMemberOrAdmin() ? (
              <Button className="flex items-center space-x-2">
                <Plus className="h-4 w-4" />
                <span>Create Project</span>
              </Button>
            ) : undefined
          }
        />
      )}

      {/* Demo Instructions */}
      {isDemo() && (
        <Card className="demo-banner">
          <CardContent className="p-6">
            <h3 className="font-semibold mb-2">Selamat datang di Mode Demo!</h3>
            <p className="text-sm mb-4">
              Anda sedang melihat data contoh dari coffee shop. Dalam mode demo, Anda dapat:
            </p>
            <ul className="text-sm space-y-1 list-disc list-inside">
              <li>Melihat analytics dan insights</li>
              <li>Menggunakan filter dan sort</li>
              <li>Menjelajahi semua fitur dashboard</li>
            </ul>
            <p className="text-sm mt-4">
              Untuk menganalisis data Anda sendiri, 
              <Button variant="link" className="p-0 h-auto text-blue-700 underline ml-1">
                buat akun member gratis
              </Button>.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
