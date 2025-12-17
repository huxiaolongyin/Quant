<template>
  <div ref="chartRef" class="w-full h-full"></div>
</template>

<script setup lang="ts">
import * as echarts from "echarts";
import { nextTick, onMounted, onUnmounted, ref, watch } from "vue";

const props = defineProps<{
  data: {
    dates: string[];
    values: number[][]; // [Open, Close, Low, High]
    volumes: number[];
  };
  title?: string;
}>();

const chartRef = ref<HTMLElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

// 配置项生成函数
const getOption = () => {
  const { dates, values, volumes } = props.data;

  // 计算涨跌颜色 (中国标准：红涨绿跌)
  const upColor = "#ef4444"; // Tailwind red-500
  const downColor = "#22c55e"; // Tailwind green-500

  return {
    title: { text: props.title || "", left: 0 },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "cross" },
      backgroundColor: "rgba(255, 255, 255, 0.9)",
      borderColor: "#ccc",
      borderWidth: 1,
      textStyle: { color: "#333" },
    },
    axisPointer: { link: [{ xAxisIndex: "all" }] },
    grid: [
      { left: "10%", right: "8%", height: "50%" }, // K线区域
      { left: "10%", right: "8%", top: "65%", height: "15%" }, // 成交量区域
    ],
    xAxis: [
      {
        type: "category",
        data: dates,
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false },
        min: "dataMin",
        max: "dataMax",
      },
      {
        type: "category",
        gridIndex: 1,
        data: dates,
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        min: "dataMin",
        max: "dataMax",
      },
    ],
    yAxis: [
      {
        scale: true,
        splitArea: { show: true },
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
      },
    ],
    dataZoom: [
      { type: "inside", xAxisIndex: [0, 1], start: 50, end: 100 },
      { show: true, xAxisIndex: [0, 1], type: "slider", bottom: 10, start: 50, end: 100 },
    ],
    series: [
      {
        name: "日K",
        type: "candlestick",
        data: values,
        itemStyle: {
          color: upColor,
          color0: downColor,
          borderColor: upColor,
          borderColor0: downColor,
        },
      },
      {
        name: "MA5",
        type: "line",
        data: calculateMA(5, values),
        smooth: true,
        showSymbol: false,
        lineStyle: { opacity: 0.5 },
      },
      {
        name: "Volume",
        type: "bar",
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes.map((vol, i) => {
          return {
            value: vol,
            itemStyle: {
              color: values[i][1] > values[i][0] ? upColor : downColor,
            },
          };
        }),
      },
    ],
  };
};

// 辅助函数：计算均线
function calculateMA(dayCount: number, data: number[][]) {
  const result = [];
  for (let i = 0, len = data.length; i < len; i++) {
    if (i < dayCount) {
      result.push("-");
      continue;
    }
    let sum = 0;
    for (let j = 0; j < dayCount; j++) {
      sum += +data[i - j][1]; // Close price
    }
    result.push((sum / dayCount).toFixed(2));
  }
  return result;
}

// 初始化图表
const initChart = () => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value);
    chartInstance.setOption(getOption());
  }
};

onMounted(() => {
  nextTick(() => {
    initChart();
    window.addEventListener("resize", handleResize);
  });
});

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  chartInstance?.dispose();
});

const handleResize = () => chartInstance?.resize();

// 监听数据变化
watch(
  () => props.data,
  () => {
    chartInstance?.setOption(getOption(), true); // true = not merge, complete update
  },
  { deep: true }
);

// 暴露 resize 方法给父组件（如果 Drawer 动画导致尺寸不对时调用）
defineExpose({ resize: handleResize });
</script>
