import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { 
  Plus, 
  Download, 
  Filter, 
  Search,
  MessageSquare,
  Brain,
  Zap as ZapIcon
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingState, EmptyState } from '@/components/ui/loading'
import { Badge } from '@/components/ui/badge'
import { isDemo, isMemberOrAdmin } from '@/store/auth'
import { api } from '@/services/api'
import { formatRelativeTime, getUrgencyColor, truncateText } from '@/lib/utils'

export function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [searchTerm, setSearchTerm] = useState('')
  const [activeTab, setActiveTab] = useState<'feedbacks' | 'insights' | 'automation'>('feedbacks')

  // Get project details
  const { data: projectData, isLoading: projectLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectId ? api.getProject(projectId) : null,
    enabled: !!projectId,
  })

  // Get project feedbacks
  const { data: feedbacksData, isLoading: feedbacksLoading } = useQuery({
    queryKey: ['project-feedbacks', projectId],
    queryFn: () => projectId ? api.getProjectFeedbacks(projectId) : null,
    enabled: !!projectId,
  })

  // Get automation jobs
  const { data: jobsData, isLoading: jobsLoading } = useQuery({
    queryKey: ['orchestrate-jobs', projectId],
    queryFn: () => projectId ? api.getOrchestrateJobs(projectId) : null,
    enabled: !!projectId && activeTab === 'automation',
  })

  const project = projectData?.data
  const feedbacks = feedbacksData?.data?.feedbacks || []
  const jobs = jobsData?.data?.jobs || []

  if (projectLoading) {
    return <LoadingState message="Loading project..." />
  }

  if (!project) {
    return (
      <EmptyState
        title="Project not found"
        description="The project you're looking for doesn't exist or you don't have access to it."
      />
    )
  }

  const filteredFeedbacks = feedbacks.filter(feedback =>
    feedback.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
    feedback.author_name?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const tabs = [
    { id: 'feedbacks', label: 'Feedbacks', icon: MessageSquare, count: feedbacks.length },
    { id: 'insights', label: 'Insights', icon: Brain, count: feedbacks.filter(f => f.analysis).length },
    { id: 'automation', label: 'Automation', icon: ZapIcon, count: jobs.length },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              {project.name}
            </h1>
            {project.is_demo && (
              <Badge variant="secondary">Demo</Badge>
            )}
          </div>
          {project.description && (
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              {project.description}
            </p>
          )}
        </div>
        
        <div className="flex items-center space-x-3">
          {isMemberOrAdmin() && (
            <>
              <Button variant="outline" className="flex items-center space-x-2">
                <Download className="h-4 w-4" />
                <span>Export</span>
              </Button>
              <Button className="flex items-center space-x-2">
                <Plus className="h-4 w-4" />
                <span>Add Feedback</span>
              </Button>
            </>
          )}
          
          {isDemo() && (
            <div className="flex items-center space-x-2 text-sm text-blue-600">
              <span>Demo Mode</span>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              <span>{tab.label}</span>
              <span className="bg-gray-100 text-gray-600 rounded-full px-2 py-1 text-xs">
                {tab.count}
              </span>
            </button>
          ))}
        </nav>
      </div>

      {/* Search and Filters */}
      {(activeTab === 'feedbacks' || activeTab === 'insights') && (
        <div className="flex items-center space-x-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search feedbacks..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button variant="outline" className="flex items-center space-x-2">
            <Filter className="h-4 w-4" />
            <span>Filters</span>
          </Button>
        </div>
      )}

      {/* Content */}
      <div className="space-y-6">
        {activeTab === 'feedbacks' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            {feedbacksLoading ? (
              <LoadingState message="Loading feedbacks..." />
            ) : filteredFeedbacks.length === 0 ? (
              <EmptyState
                title="No feedbacks found"
                description={
                  searchTerm 
                    ? "No feedbacks match your search criteria."
                    : "No feedbacks have been added to this project yet."
                }
                action={
                  isMemberOrAdmin() ? (
                    <Button className="flex items-center space-x-2">
                      <Plus className="h-4 w-4" />
                      <span>Add First Feedback</span>
                    </Button>
                  ) : undefined
                }
              />
            ) : (
              <div className="grid gap-4">
                {filteredFeedbacks.map((feedback) => (
                  <motion.div
                    key={feedback.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <Card className="hover:shadow-md transition-shadow">
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex-1">
                            <p className="text-gray-900 dark:text-white mb-2">
                              {feedback.content}
                            </p>
                            <div className="flex items-center space-x-4 text-sm text-gray-500">
                              {feedback.author_name && (
                                <span>by {feedback.author_name}</span>
                              )}
                              <span className="capitalize">{feedback.source}</span>
                              <span>{formatRelativeTime(feedback.created_at)}</span>
                            </div>
                          </div>
                          
                          {feedback.analysis && (
                            <div className="flex items-center space-x-2 ml-4">
                              {feedback.analysis.sentiment_label && (
                                <Badge 
                                  variant={
                                    feedback.analysis.sentiment_label === 'positive' ? 'positive' :
                                    feedback.analysis.sentiment_label === 'negative' ? 'negative' : 'neutral'
                                  }
                                  className="capitalize"
                                >
                                  {feedback.analysis.sentiment_label}
                                </Badge>
                              )}
                              
                              {feedback.analysis.granite_insights?.urgency && (
                                <Badge 
                                  variant="outline"
                                  className={getUrgencyColor(feedback.analysis.granite_insights.urgency)}
                                >
                                  {feedback.analysis.granite_insights.urgency} urgency
                                </Badge>
                              )}
                            </div>
                          )}
                        </div>
                        
                        {feedback.analysis?.topics && feedback.analysis.topics.length > 0 && (
                          <div className="flex flex-wrap gap-2 mt-3">
                            {feedback.analysis.topics.slice(0, 3).map((topic, index) => (
                              <Badge key={index} variant="outline" className="text-xs">
                                {topic.label}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}

        {activeTab === 'insights' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <div className="grid gap-6">
              {filteredFeedbacks
                .filter(feedback => feedback.analysis)
                .map((feedback) => (
                  <Card key={feedback.id} className="hover:shadow-md transition-shadow">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-lg mb-2">
                            {truncateText(feedback.content, 80)}
                          </CardTitle>
                          <CardDescription>
                            {feedback.analysis?.granite_summary}
                          </CardDescription>
                        </div>
                        
                        <div className="flex items-center space-x-2 ml-4">
                          {feedback.analysis?.sentiment_label && (
                            <Badge 
                              variant={
                                feedback.analysis.sentiment_label === 'positive' ? 'positive' :
                                feedback.analysis.sentiment_label === 'negative' ? 'negative' : 'neutral'
                              }
                            >
                              {feedback.analysis.sentiment_label}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      {feedback.analysis?.granite_insights?.action_recommendation && (
                        <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg">
                          <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
                            Recommended Action
                          </h4>
                          <p className="text-sm text-blue-800 dark:text-blue-200">
                            {feedback.analysis.granite_insights.action_recommendation}
                          </p>
                        </div>
                      )}
                      
                      {feedback.analysis?.topics_fixed && feedback.analysis.topics_fixed.length > 0 && (
                        <div className="mt-4">
                          <h4 className="font-medium mb-2">Topics</h4>
                          <div className="flex flex-wrap gap-2">
                            {feedback.analysis.topics_fixed.map((topic, index) => (
                              <Badge key={index} variant="outline">
                                {topic.label} ({(topic.score * 100).toFixed(1)}%)
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
            </div>
          </motion.div>
        )}

        {activeTab === 'automation' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            {jobsLoading ? (
              <LoadingState message="Loading automation jobs..." />
            ) : jobs.length === 0 ? (
              <EmptyState
                title="No automation jobs"
                description="No automated actions have been triggered for this project yet."
              />
            ) : (
              <div className="grid gap-4">
                {jobs.map((job) => (
                  <Card key={job.id}>
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-medium text-gray-900 dark:text-white capitalize">
                            {job.kind} Job
                          </h3>
                          <p className="text-sm text-gray-500 mt-1">
                            Created {formatRelativeTime(job.created_at)}
                          </p>
                        </div>
                        <Badge 
                          variant={
                            job.status === 'completed' ? 'positive' :
                            job.status === 'failed' ? 'negative' : 'outline'
                          }
                        >
                          {job.status}
                        </Badge>
                      </div>
                      
                      {job.error_message && (
                        <div className="mt-4 p-3 bg-red-50 dark:bg-red-950 rounded-lg">
                          <p className="text-sm text-red-800 dark:text-red-200">
                            {job.error_message}
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </div>

      {/* Demo Notice */}
      {isDemo() && (
        <Card className="demo-banner">
          <CardContent className="p-4">
            <p className="text-sm">
              <strong>Mode Demo:</strong> Anda sedang melihat data contoh. 
              Fitur seperti "Add Feedback" dan "Export" hanya tersedia untuk Member.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
