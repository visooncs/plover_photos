<template>
  <div class="h-full flex flex-col bg-gray-50 overflow-hidden">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between shrink-0">
      <h1 class="text-2xl font-bold text-gray-800">系统维护</h1>
      <button 
        @click="refresh" 
        class="p-2 hover:bg-gray-100 rounded-full text-gray-600 transition-colors"
        title="刷新状态"
      >
        <RefreshCw :size="20" :class="{ 'animate-spin': maintenanceStore.loading }" />
      </button>
    </header>

    <div class="flex-1 overflow-auto p-6">
      <div class="max-w-6xl mx-auto space-y-8">
        
        <!-- Quick Actions / Create Task -->
        <section>
          <h2 class="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <Play :size="20" />
            <span>执行任务</span>
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div v-for="cmd in availableCommands" :key="cmd.id" 
                 class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
              <div class="flex items-start justify-between mb-2">
                <component :is="cmd.icon" class="text-blue-600" :size="24" />
                <button 
                  @click="triggerTask(cmd)"
                  class="px-3 py-1 bg-blue-50 text-blue-600 rounded-lg text-sm font-medium hover:bg-blue-100 transition-colors"
                >
                  运行
                </button>
              </div>
              <h3 class="font-medium text-gray-800">{{ cmd.title }}</h3>
              <p class="text-sm text-gray-500 mt-1">{{ cmd.description }}</p>
            </div>
          </div>
        </section>

        <!-- Scheduled Tasks -->
        <section>
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold text-gray-700 flex items-center gap-2">
              <Calendar :size="20" />
              <span>定时任务</span>
            </h2>
            <button 
              @click="openAddScheduleModal"
              class="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 font-medium px-3 py-1.5 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
            >
              <Plus :size="16" />
              <span>添加计划</span>
            </button>
          </div>
          
          <div v-if="maintenanceStore.schedules.length === 0" class="text-center py-8 bg-white rounded-xl border border-gray-200 border-dashed">
             <div class="text-gray-400 mb-2"><Calendar :size="32" class="mx-auto" /></div>
            <p class="text-gray-500">暂无定时任务</p>
          </div>
          
          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div v-for="sched in maintenanceStore.schedules" :key="sched.id" 
                 class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex items-start justify-between">
              <div>
                <h3 class="font-medium text-gray-800">{{ getTaskTitle(sched.name) }}</h3>
                <div class="text-sm text-gray-500 mt-1 flex items-center gap-2">
                  <Clock :size="14" />
                  <span>
                    {{ sched.schedule_type === 'daily' ? '每天' : 
                       sched.schedule_type === 'weekly' ? '每周' : '间隔' }} 
                    {{ sched.schedule_value }}
                    {{ sched.schedule_type === 'interval' ? '分钟' : '' }}
                  </span>
                </div>
                <div class="text-xs text-gray-400 mt-2">
                  上次运行: {{ sched.last_run_at ? formatDate(sched.last_run_at) : '从未' }}
                </div>
              </div>
              
              <button 
                @click="maintenanceStore.deleteSchedule(sched.id)"
                class="text-gray-400 hover:text-red-500 p-1 rounded-md hover:bg-red-50 transition-colors"
                title="删除计划"
              >
                <Trash2 :size="16" />
              </button>
            </div>
          </div>
        </section>

        <!-- Active & Recent Tasks -->
        <section>
          <h2 class="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <Activity :size="20" />
            <span>任务队列</span>
          </h2>
          
          <div v-if="maintenanceStore.tasks.length === 0" class="text-center py-12 bg-white rounded-xl border border-gray-200 border-dashed">
            <div class="text-gray-400 mb-2"><CheckCircle :size="48" class="mx-auto" /></div>
            <p class="text-gray-500">当前没有任务</p>
          </div>

          <div v-else class="space-y-4">
            <div v-for="task in maintenanceStore.tasks" :key="task.id" 
                 class="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              
              <!-- Task Header -->
              <div class="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors" @click="toggleExpand(task.id)">
                <div class="flex items-center gap-4">
                  <div class="text-gray-400 transition-transform duration-200" :class="{ 'rotate-90': isExpanded(task) }">
                    <ChevronRight :size="16" />
                  </div>
                  <div :class="statusColor(task.status)" class="p-2 rounded-lg bg-opacity-10">
                    <component :is="statusIcon(task.status)" :size="20" :class="{ 'animate-spin': task.status === 'running' }" />
                  </div>
                  <div>
                    <h3 class="font-medium text-gray-800">{{ getTaskTitle(task.name) }}</h3>
                    <div class="text-xs text-gray-500 flex items-center gap-2">
                      <span>ID: {{ task.id.slice(0, 8) }}</span>
                      <span>•</span>
                      <span>{{ formatDate(task.created_at) }}</span>
                      <span v-if="task.finished_at">• 耗时: {{ getDuration(task) }}</span>
                    </div>
                  </div>
                </div>

                <div class="flex items-center gap-3">
                   <span :class="statusBadge(task.status)" class="px-2.5 py-0.5 rounded-full text-xs font-medium capitalize">
                     {{ statusText(task.status) }}
                   </span>
                   <button 
                     v-if="task.status === 'pending' || task.status === 'failed' || task.status === 'completed'"
                     @click.stop="deleteTask(task.id)"
                     class="text-gray-400 hover:text-red-500 p-1"
                     title="删除记录"
                   >
                     <Trash2 :size="16" />
                   </button>
                   <button 
                     v-if="task.status === 'failed' || task.status === 'completed'"
                     @click.stop="rerunTask(task)"
                     class="text-gray-400 hover:text-blue-500 p-1"
                     title="重新运行"
                   >
                     <RotateCw :size="16" />
                   </button>
                </div>
              </div>

              <!-- Collapsible Content -->
              <div v-show="isExpanded(task)">
                <!-- Progress Bar (for running tasks) -->
                <div v-if="task.status === 'running'" class="px-4 pb-4">
                  <div class="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div 
                      class="h-full bg-blue-500 transition-all duration-500 ease-out"
                      :style="{ width: `${task.progress || 5}%` }"
                    ></div>
                  </div>
                  <div class="mt-1 flex justify-between text-xs text-gray-500">
                    <span>正在执行中...</span>
                    <span>{{ task.progress }}%</span>
                  </div>
                </div>

                <!-- Logs (Expandable) -->
                <div v-if="task.logs || task.error_message" class="bg-gray-900 text-gray-300 text-xs p-4 font-mono overflow-x-auto max-h-48 border-t border-gray-100">
                  <div v-if="task.error_message" class="text-red-400 mb-2">Error: {{ task.error_message }}</div>
                  <pre class="whitespace-pre-wrap">{{ task.logs }}</pre>
                </div>
              </div>
            </div>
          </div>
        </section>

      </div>
    </div>

    <!-- Add Schedule Modal -->
    <div v-if="showAddScheduleModal" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl w-full max-w-md p-6 shadow-xl">
        <h3 class="text-lg font-bold text-gray-900 mb-4">添加定时任务</h3>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">任务类型</label>
            <select v-model="newSchedule.name" class="w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500">
              <option v-for="cmd in availableCommands" :key="cmd.name" :value="cmd.name">
                {{ cmd.title }}
              </option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">调度类型</label>
            <select v-model="newSchedule.schedule_type" class="w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500">
              <option value="daily">每天</option>
              <option value="weekly">每周</option>
              <option value="interval">间隔</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              {{ newSchedule.schedule_type === 'daily' ? '时间 (HH:MM)' : 
                 newSchedule.schedule_type === 'weekly' ? '时间 (d HH:MM, 0=周一)' : '间隔 (分钟)' }}
            </label>
            <input 
              v-model="newSchedule.schedule_value" 
              type="text" 
              class="w-full rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500"
              :placeholder="newSchedule.schedule_type === 'daily' ? '03:00' : newSchedule.schedule_type === 'interval' ? '60' : '0 03:00'"
            >
          </div>
        </div>
        
        <div class="mt-6 flex justify-end gap-3">
          <button 
            @click="showAddScheduleModal = false"
            class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            取消
          </button>
          <button 
            @click="saveSchedule"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            保存
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useMaintenanceStore } from '../stores/maintenance';
import { 
  RefreshCw, Play, Activity, CheckCircle, Clock, AlertTriangle, 
  Trash2, RotateCw, Database, Camera, Users, Brain, MapPin, Search, Calendar, Plus, ChevronRight
} from 'lucide-vue-next';
import { format, formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { ref, reactive, onMounted, onUnmounted } from 'vue';
import { storeToRefs } from 'pinia';

const maintenanceStore = useMaintenanceStore();

// --- Expanded state logic ---
const expandedTasks = ref(new Set());

const toggleExpand = (id) => {
  if (expandedTasks.value.has(id)) {
    expandedTasks.value.delete(id);
  } else {
    expandedTasks.value.add(id);
  }
};

const isExpanded = (task) => {
  // Always expand running tasks by default if not explicitly toggled?
  // Or just initialize running tasks as expanded.
  // Let's rely on the set.
  if (task.status === 'running') return true;
  return expandedTasks.value.has(task.id);
};
const showAddScheduleModal = ref(false);
const newSchedule = reactive({
  name: 'scan_photos',
  schedule_type: 'daily',
  schedule_value: '03:00',
  params: {}
});

const openAddScheduleModal = () => {
  newSchedule.name = availableCommands[0].name;
  newSchedule.schedule_type = 'daily';
  newSchedule.schedule_value = '03:00';
  showAddScheduleModal.value = true;
};

const saveSchedule = async () => {
  const success = await maintenanceStore.createSchedule({ ...newSchedule });
  if (success) {
    showAddScheduleModal.value = false;
  }
};

const availableCommands = [
  { id: 'scan_photos', name: 'scan_photos', title: '扫描照片库', description: '扫描指定目录下的所有新照片', icon: Database },
  { id: 'process_embeddings', name: 'process_embeddings', title: '生成语义向量', description: '为照片生成 AI 语义特征，用于搜索', icon: Brain },
  { id: 'update_gps', name: 'update_gps', title: '更新位置信息', description: '解析 GPS 坐标并获取地理位置名称', icon: MapPin },
  { id: 'process_faces', name: 'process_faces', title: '人脸识别', description: '检测照片中的人脸并提取特征', icon: Users },
  { id: 'cluster_people', name: 'cluster_people', title: '人脸聚类', description: '将相似的人脸归类为同一个人', icon: Users },
  { id: 'generate_memories', name: 'generate_memories', title: '生成回忆', description: '基于时间生成"那年今日"等回忆', icon: Camera },
  { id: 'cleanup_trash', name: 'cleanup_trash', title: '清空回收站', description: '彻底删除回收站中的照片', icon: Trash2 },
];

const refresh = () => maintenanceStore.fetchTasks();

// Auto refresh
let timer;
onMounted(async () => {
  await refresh();
  // Expand all running tasks initially
  maintenanceStore.tasks.forEach(t => {
    if (t.status === 'running') {
      expandedTasks.value.add(t.id);
    }
  });
  timer = setInterval(refresh, 2000); // Poll every 2s
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});

const triggerTask = async (cmd) => {
  // Simple trigger for now. Later we can add a dialog for params.
  const params = {};
  if (cmd.name === 'scan_photos') {
      // Default path? Or just scan all libraries?
      // The command currently requires a path arg.
      // We should probably update the backend command to use default library path if not provided.
      // For now, let's assume the backend handles it or we hardcode a common path.
      // Actually, let's prompt user or just pass a flag.
      // To make it robust, let's assume scan_photos scans configured libraries.
  }
  
  const newTask = await maintenanceStore.createTask(cmd.name, params);
  if (newTask) {
    // Auto run
    await maintenanceStore.runTask(newTask.id);
  }
};

const deleteTask = (id) => maintenanceStore.deleteTask(id);

const rerunTask = async (task) => {
  // Create new task with same params
  const newTask = await maintenanceStore.createTask(task.name, task.params);
  if (newTask) {
    await maintenanceStore.runTask(newTask.id);
  }
};

const getTaskTitle = (name) => {
  const cmd = availableCommands.find(c => c.name === name);
  return cmd ? cmd.title : name;
};

const statusIcon = (status) => {
  switch (status) {
    case 'running': return RefreshCw; // Should animate
    case 'completed': return CheckCircle;
    case 'failed': return AlertTriangle;
    default: return Clock;
  }
};

const statusColor = (status) => {
  switch (status) {
    case 'running': return 'text-blue-600 bg-blue-100';
    case 'completed': return 'text-green-600 bg-green-100';
    case 'failed': return 'text-red-600 bg-red-100';
    default: return 'text-gray-600 bg-gray-100';
  }
};

const statusBadge = (status) => {
  switch (status) {
    case 'running': return 'text-blue-700 bg-blue-50 border border-blue-100';
    case 'completed': return 'text-green-700 bg-green-50 border border-green-100';
    case 'failed': return 'text-red-700 bg-red-50 border border-red-100';
    default: return 'text-gray-700 bg-gray-50 border border-gray-100';
  }
};

const statusText = (status) => {
    const map = {
        'pending': '等待中',
        'running': '执行中',
        'completed': '已完成',
        'failed': '失败'
    }
    return map[status] || status;
}

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return format(new Date(dateStr), 'yyyy-MM-dd HH:mm:ss');
};

const getDuration = (task) => {
  if (!task.started_at || !task.finished_at) return '';
  const start = new Date(task.started_at);
  const end = new Date(task.finished_at);
  const diff = (end - start) / 1000;
  if (diff < 60) return `${diff.toFixed(1)}秒`;
  return `${(diff / 60).toFixed(1)}分钟`;
};
</script>
