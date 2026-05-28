"use client";
import { text2 as mText2 } from '@/lib/colors';

const FieldLabel=({children,required=false})=><div style={{fontSize:12,fontWeight:600,color:mText2,marginBottom:6}}>
    {children}{required&&<span style={{color:'#c0394a',marginLeft:4}}>*</span>}
  </div>;
export default FieldLabel;
export { FieldLabel };
