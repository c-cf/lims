"use client";
import React from 'react';
import MgrDashboard from '@/components/Manager/MgrDashboard';
import MgrAllRequests from '@/components/Manager/MgrAllRequests';
import MgrRequestDetail from '@/components/Manager/MgrRequestDetail';
import MgrRecipes from '@/components/Manager/MgrRecipes';
import MgrReports from '@/components/Manager/MgrReports';
import { ink as mInk } from '@/lib/colors';

const MgrApp=({route,navigate})=>{const[toast,setToast]=React.useState(null);const showToast=msg=>{setToast(msg);setTimeout(()=>setToast(null),2200);};let page=null;const p=route.page;if(p==='mgr_dashboard')page=<MgrDashboard navigate={navigate}/>;else if(p==='mgr_all_requests')page=<MgrAllRequests navigate={navigate}/>;else if(p==='mgr_request')page=<MgrRequestDetail id={route.id}navigate={navigate}showToast={showToast}/>;else if(p==='mgr_recipes')page=<MgrRecipes showToast={showToast}/>;else if(p==='mgr_reports')page=<MgrReports/>;else page=<MgrDashboard navigate={navigate}/>;return<>
      {page}
      {toast&&<div style={{position:'fixed',bottom:28,left:'50%',transform:'translateX(-50%)',padding:'12px 20px',borderRadius:10,background:mInk,color:'#fff',fontSize:14,fontWeight:500,boxShadow:'0 12px 36px rgba(20,20,28,0.32)',animation:'slide-in 0.18s ease-out',zIndex:300}}>{toast}</div>}
    </>;};
export default MgrApp;
export { MgrApp };
