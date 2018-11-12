import Vue from 'vue';
import InstallerIssue from '@/components/InstallerIssue';

describe('InstallerIssue.vue', () => {
  it('should render correct contents', () => {
    const Constructor = Vue.extend(InstallerIssue);
    const vm = new Constructor().$mount();
    expect(vm.$el.querySelector('.hello h1').textContent).toEqual('bliu');
  });
});
