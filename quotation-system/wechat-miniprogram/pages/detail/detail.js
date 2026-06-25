Page({
  data: {
    quotation: {
      company: "太仓明邦陈列展示用品有限公司",
      title: "报价单",
      projectSets: "1",
      date: "",
      itemCount: 0,
      items: [],
      totalAmount: "0.00"
    }
  },

  onLoad() {
    const quotation = wx.getStorageSync("mobileQuotationDetail");
    if (quotation && Array.isArray(quotation.items)) {
      this.setData({ quotation });
    }
  },

  goBack() {
    wx.navigateBack();
  }
});
