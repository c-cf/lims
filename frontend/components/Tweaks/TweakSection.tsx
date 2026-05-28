"use client";


function TweakSection({label,children=undefined}){return<>
      <div className="twk-sect">{label}</div>
      {children}
    </>;}
export default TweakSection;
export { TweakSection };
