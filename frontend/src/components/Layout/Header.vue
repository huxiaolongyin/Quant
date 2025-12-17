<template>
  <header
    class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm z-10"
  >
    <!-- Breadcrumb or Title -->
    <h2 class="text-lg font-semibold text-gray-700">
      {{ $route.meta.title || "Quant Platform" }}
    </h2>

    <!-- Right Actions -->
    <div class="flex items-center space-x-4">
      <div class="text-right mr-4">
        <div class="text-xs text-gray-500">可用资金</div>
        <div class="text-sm font-bold text-gray-800">¥ 1,240,500.00</div>
      </div>
      <div
        class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold border border-blue-200"
      >
        A
      </div>
    </div>
  </header>
</template>
