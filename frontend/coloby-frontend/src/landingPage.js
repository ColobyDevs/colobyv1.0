import React, {useContext} from 'react'
import { Context } from './context/context'

const LandingPage =()=> {
    const {coloby} = useContext(Context)
  return (
    <div className='text-xl'>{coloby}, hi</div>
  )
}
export default LandingPage