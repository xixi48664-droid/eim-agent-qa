<template>
  <div class="home-page">
    <el-card class="hero-card">
      <div class="hero-title">主问答</div>
      <div class="hero-desc">这是用户端首页入口，后续在这里接入写死问答和智能引导。</div>
    </el-card>

    <el-card class="quick-card">
      <template #header>
        <div class="section-title">快捷入口</div>
      </template>

      <div class="quick-grid">
        <div class="quick-item">拍照识件</div>
        <div class="quick-item">参数查询</div>
        <div class="quick-item">规范问答</div>
        <div class="quick-item">流程指导</div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.home-page {
  display: grid;
  gap: 16px;
}

.hero-card {
  min-height: 180px;
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
}

.hero-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 12px;
}

.hero-desc {
  color: #6b7280;
}

.section-title {
  font-weight: 600;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.quick-item {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 18px;
  background: #f9fbff;
  text-align: center;
}
</style>
