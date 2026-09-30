"""Three bounded columns: fixed outer edges, movable internal dividers."""
MINIMUMS=(80,36,36)

def fit_columns(total,widths):
 total=max(sum(MINIMUMS),int(total))
 right=max(72,min(total-80,int(widths[1])+int(widths[2])))
 extra=right-72;old=max(0,widths[1]-36)+max(0,widths[2]-36)
 view=36+round(extra*(max(0,widths[1]-36)/old if old else .5))
 return (total-right,view,right-view)

def move_divider(widths,index,delta):
 a,b,c=widths;total=a+b+c
 if index==1:
  b=max(36,min(b+c-36,b+delta));return (a,b,total-a-b)
 new_a=max(80,min(total-72,a+delta));right=total-new_a
 # Distribute available width across both right columns, preserving their excess ratio.
 extra=right-72;old=max(0,b-36)+max(0,c-36)
 new_b=36+round(extra*((b-36)/old if old else .5))
 return (new_a,new_b,right-new_b)
