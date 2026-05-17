import request from './request'

export const getTutorialByProcessApi = (processName) => {
  return request.get('/tutorials/guide', {
    params: { processName },
  })
}

export const getTutorialDetailApi = (tutorialId) => {
  return request.get(`/tutorials/guide/${tutorialId}`)
}
