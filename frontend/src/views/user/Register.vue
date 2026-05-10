<template>
  <div class="placeholder-page">
    <el-card class="placeholder-card">
      <template #header>注册页面</template>
      <p>注册接口尚未在当前前端联调阶段接入，这里先作为占位页。</p>
      <p>后续后端给出注册接口后，可在此完成真实表单与提交逻辑。</p>
      <el-button type="primary" @click="$router.push('/login')">返回登录</el-button>
    </el-card>
  </div>
</template>

<style scoped>
.placeholder-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  box-sizing: border-box;
}
.placeholder-card {
  width: min(520px, 100%);
}
</style>
