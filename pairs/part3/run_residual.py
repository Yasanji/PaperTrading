import pickle, time, model_residual as M
t = time.time(); pa, ex = M.run(); print('base', round(time.time()-t), 's', flush=True)
best = ex['contrib'].index[0]; pa2, ex2 = M.run(exclude_ind=(best,)); print('ex-best done:', best, flush=True)
pickle.dump(dict(pa=pa, ex={'contrib': ex['contrib']}, pa2=pa2, best=best), open('results_residual.pkl','wb'))
