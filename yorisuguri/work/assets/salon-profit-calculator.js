/* Private, local-only salon calculation. No tracking or data collection. */
(function () {
  "use strict";
  var yen = new Intl.NumberFormat("ja-JP", { style: "currency", currency: "JPY", maximumFractionDigits: 0 });
  var num = new Intl.NumberFormat("ja-JP", { maximumFractionDigits: 1 });
  function recalc(form) {
    function n(key) { var e=form.elements.namedItem(key); return e?Number(e.value):NaN; }
    function put(key,value) { var e=form.querySelector('[data-output="'+key+'"]'); if(e)e.textContent=value; }
    var fixed=n("fixed"),price=n("price"),cost=n("cost"),days=n("days"),
        slots=n("slots"),visits=n("visits"),startup=n("startup");
    var values=[fixed,price,cost,days,slots,visits,startup];
    var ok=values.every(function(x){return Number.isFinite(x)&&x>=0;})&&days>0&&slots>0&&price>cost;
    var summary=form.querySelector("[data-summary]");
    if(!ok){
      ["required","per-day","utilization","profit","payback"].forEach(function(k){put(k,"—");});
      if(summary)summary.textContent="入力を確認してください。客単価は1人あたり変動費を上回る必要があります。";
      return;
    }
    var margin=price-cost,need=Math.ceil(fixed/margin),capacity=days*slots,
        rate=100*need/capacity,profit=visits*margin-fixed;
    put("required",num.format(need)+"人");
    put("per-day",num.format(need/days)+"人");
    put("utilization",num.format(rate)+"%");
    put("profit",yen.format(profit));
    put("payback",profit>0?num.format(startup/profit)+"か月":"回収不可");
    if(summary){
      summary.textContent=need>capacity
        ?"現在の予約枠を全部埋めても固定費を回収できない条件です。客単価・費用・枠数を見直してください。"
        :"月"+num.format(need)+"人が損益分岐の目安。月間最大"+num.format(capacity)+"枠と比較してください。";
    }
  }
  document.addEventListener("DOMContentLoaded",function(){
    document.querySelectorAll("[data-salon-calculator]").forEach(function(form){
      form.addEventListener("input",function(){recalc(form);});
      form.addEventListener("change",function(){recalc(form);});
      form.addEventListener("submit",function(e){e.preventDefault();recalc(form);});
      recalc(form);
    });
  });
})();